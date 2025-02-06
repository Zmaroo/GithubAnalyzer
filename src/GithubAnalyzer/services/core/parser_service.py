"""Parser service for code analysis using tree-sitter."""
import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set, Union

from tree_sitter import Language, Parser, Tree

from GithubAnalyzer.models.core.ast import ParseResult
from GithubAnalyzer.models.core.errors import LanguageError, ParserError
from GithubAnalyzer.models.core.file import FileInfo
from GithubAnalyzer.models.core.traversal import TreeSitterTraversal
from GithubAnalyzer.services.analysis.parsers.language_service import \
    LanguageService
from GithubAnalyzer.services.parsers.core.query_handler import \
    TreeSitterQueryHandler
from GithubAnalyzer.services.analysis.parsers.utils import (
    find_common_ancestor, get_node_hierarchy, get_node_text, iter_children,
    node_to_dict)
from GithubAnalyzer.utils.logging import get_logger, get_tree_sitter_logger
from GithubAnalyzer.utils.timing import timer

# Initialize logger
logger = get_logger("core.parser")
ts_logger = get_tree_sitter_logger()

# Special file types that don't need parsing
LICENSE_FILES = {'license', 'license.txt', 'license.md', 'copying', 'copying.txt', 'copying.md'}

@dataclass
class ParserService:
    """Service for parsing files using tree-sitter."""
    
    def __post_init__(self):
        """Initialize the parser service."""
        self._logger = logger
        self._start_time = time.time()
        self._language_service = LanguageService()
        self._query_handler = TreeSitterQueryHandler()
        
        self._log("debug", "Parser service initialized",
                 supported_languages=list(self._language_service.supported_languages))
        
    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """Get standard context for logging.
        
        Args:
            **kwargs: Additional context key-value pairs
            
        Returns:
            Dict with standard context fields plus any additional fields
        """
        context = {
            'module': 'parser',
            'thread': threading.get_ident(),
            'duration_ms': (time.time() - self._start_time) * 1000
        }
        context.update(kwargs)
        return context
        
    def _log(self, level: str, message: str, **kwargs) -> None:
        """Log with consistent context.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Message to log
            **kwargs: Additional context key-value pairs
        """
        context = self._get_context(**kwargs)
        getattr(self._logger, level)(message, extra={'context': context})
        
    @timer
    def parse_file(self, file_path: Union[str, Path], language: Optional[str] = None) -> ParseResult:
        """Parse a file using tree-sitter.
        
        Args:
            file_path: Path to the file to parse
            language: Optional language identifier (will be detected from extension if not provided)
            
        Returns:
            ParseResult containing the tree and metadata
            
        Raises:
            LanguageError: If language is not supported
            ParserError: If parsing fails
        """
        file_path = Path(file_path)
        
        # Get language from extension if not provided
        if not language:
            language = self._language_service.get_language_for_file(str(file_path))
        
        # Create FileInfo object
        file_info = FileInfo(path=file_path, language=language)
        
        # Skip unsupported files
        if not file_info.is_supported:
            self._log("debug", "Skipping unsupported file",
                     file=str(file_path),
                     language=language)
            return ParseResult(None, None, file_info)
        
        # Try to read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            self._log("warning", "File appears to be binary",
                     file=str(file_path))
            file_info.is_supported = False
            return ParseResult(None, None, file_info)
            
        return self.parse_content(content, language)
        
    @timer
    def parse_content(self, content: str, language: str) -> ParseResult:
        """Parse content using tree-sitter.
        
        Args:
            content: Content to parse
            language: Language identifier
            
        Returns:
            ParseResult containing the tree and metadata
            
        Raises:
            LanguageError: If language is not supported
            ParserError: If parsing fails
        """
        try:
            parser = self._language_service.get_parser(language)
            
            # Set up logging callback
            def logger_callback(log_type: int, msg: str) -> None:
                level = logging.ERROR if log_type == 1 else logging.DEBUG
                ts_logger.log(level, msg, extra={
                    'context': {
                        'source': 'tree-sitter',
                        'type': 'parser',
                        'log_type': 'error' if log_type == 1 else 'parse'
                    }
                })
            
            # Set the logger on the parser
            parser.logger = logger_callback
            
            tree = parser.parse(bytes(content, "utf8"))
            if tree is None:
                raise ParserError(f"Failed to parse content for language {language}")
            
            # Get any missing or error nodes
            missing_nodes = self._query_handler.find_missing_nodes(tree.root_node)
            error_nodes = self._query_handler.find_error_nodes(tree.root_node)
            
            # Check for syntax errors but don't fail the parse
            errors = []
            if tree.root_node.has_error:
                errors.append("Syntax errors detected")
                self._log("warning", "Syntax errors detected",
                         language=language,
                         error_count=len(error_nodes))
                
            # Extract functions and other structures
            # Tree-sitter will still provide partial AST even with errors
            functions = self._query_handler.find_functions(tree.root_node, language)
            classes = self._query_handler.find_nodes(tree, "class", language)
            imports = self._query_handler.find_nodes(tree, "import", language)
            
            self._log("debug", "Content parsed successfully",
                     language=language,
                     function_count=len(functions),
                     class_count=len(classes),
                     import_count=len(imports),
                     error_count=len(error_nodes),
                     missing_count=len(missing_nodes))
            
            return ParseResult(
                tree=tree,
                language=language,
                metadata={'language': language},
                functions=functions,
                classes=classes,
                imports=imports,
                is_supported=True,  # File is supported even with syntax errors
                errors=errors,
                missing_nodes=missing_nodes,
                error_nodes=error_nodes
            )
            
        except LanguageError as e:
            self._log("error", "Language error",
                     language=language,
                     error=str(e))
            raise
        except Exception as e:
            self._log("error", "Failed to parse content",
                     language=language,
                     error=str(e))
            raise ParserError(f"Failed to parse content: {str(e)}")
            
    def get_supported_languages(self) -> Set[str]:
        """Get set of supported languages."""
        return self._language_service.supported_languages
