"""Parser service for code analysis using tree-sitter."""
import os
from pathlib import Path
from typing import Union, Optional, Callable, Dict, Any, Set
from tree_sitter import Tree, Language, Parser
import logging

from GithubAnalyzer.models.core.errors import ParserError, LanguageError
from GithubAnalyzer.models.core.ast import ParseResult
from GithubAnalyzer.models.core.file import FileInfo
from GithubAnalyzer.utils.logging import get_logger
from GithubAnalyzer.utils.timing import timer
from GithubAnalyzer.utils.logging.tree_sitter_logging import TreeSitterLogHandler
from GithubAnalyzer.services.analysis.parsers.language_service import LanguageService
from GithubAnalyzer.services.analysis.parsers.query_service import TreeSitterQueryHandler
from GithubAnalyzer.services.analysis.parsers.traversal_service import TreeSitterTraversal
from GithubAnalyzer.services.analysis.parsers.utils import (
    get_node_text,
    node_to_dict,
    iter_children,
    get_node_hierarchy,
    find_common_ancestor
)

logger = get_logger(__name__)

# Special file types that don't need parsing
LICENSE_FILES = {'license', 'license.txt', 'license.md', 'copying', 'copying.txt', 'copying.md'}

class ParserService:
    """Service for parsing files using tree-sitter."""

    def __init__(self):
        """Initialize the parser service."""
        self._language_service = LanguageService()
        self._query_handler = TreeSitterQueryHandler()
        
        # Set up tree-sitter logging
        self._ts_logger = TreeSitterLogHandler()
        self._ts_logger.setLevel(logging.DEBUG)
        logger.addHandler(self._ts_logger)
        
        # Log initialization
        logger.debug({
            "message": "Parser service initialized",
            "context": {
                "supported_languages": list(self._language_service.supported_languages)
            }
        })
        
    def __del__(self):
        """Clean up logging handlers."""
        if hasattr(self, '_ts_logger'):
            logger.removeHandler(self._ts_logger)
            
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
            return ParseResult(None, None, file_info)
        
        # Try to read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"File {file_path} appears to be binary")
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
            # Get parser for language
            parser = self._language_service.get_parser(language)
            
            # Enable tree-sitter logging for the parser
            self._ts_logger.enable_parser_logging(parser)
            
            # Parse content
            tree = parser.parse(bytes(content, 'utf-8'))
            
            # Log any tree errors
            if tree and tree.root_node:
                has_errors = self._ts_logger.log_tree_errors(tree, context=f"Parsing {language} content")
                if has_errors and logger.isEnabledFor(logging.DEBUG):
                    # Generate DOT graph for debugging
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
                        tree.print_dot_graph(f)
                        logger.debug(f"DOT graph written to {f.name}")
            
            # Validate syntax using query handler
            is_supported, errors = self._query_handler.validate_syntax(tree.root_node, language)
            
            # Extract functions and other structures
            functions = self._query_handler.find_functions(tree.root_node, language)
            classes = self._query_handler.find_nodes(tree, "class", language)
            imports = self._query_handler.find_nodes(tree, "import", language)
            
            # Get any missing or error nodes
            missing_nodes = self._query_handler.find_missing_nodes(tree.root_node)
            error_nodes = self._query_handler.find_error_nodes(tree.root_node)
            
            # Disable tree-sitter logging for the parser
            self._ts_logger.disable_parser_logging(parser)
            
            return ParseResult(
                tree=tree,
                language=language,
                metadata={'language': language},
                functions=functions,
                classes=classes,
                imports=imports,
                is_supported=is_supported,
                errors=errors,
                missing_nodes=missing_nodes,
                error_nodes=error_nodes
            )
            
        except LanguageError as e:
            logger.error(f"Language error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse content: {str(e)}")
            raise ParserError(f"Failed to parse content: {str(e)}")
            
    def get_supported_languages(self) -> Set[str]:
        """Get set of supported languages."""
        return self._language_service.supported_languages
