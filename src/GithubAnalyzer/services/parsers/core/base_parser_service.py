"""Base parser service for file parsing."""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from tree_sitter import Language, Node, Parser, Point, Query, Range, Tree

from GithubAnalyzer.models.core.ast import TreeSitterBase
from GithubAnalyzer.models.core.errors import LanguageError, ParserError
from GithubAnalyzer.models.core.file import FileInfo
from GithubAnalyzer.models.core.parsers import CustomParseResult
from GithubAnalyzer.utils.logging import get_logger, get_tree_sitter_logger
from GithubAnalyzer.utils.timing import timer

logger = get_logger(__name__)
ts_logger = get_tree_sitter_logger()

# Special file types that don't need parsing
LICENSE_FILES = {'license', 'license.txt', 'license.md', 'copying', 'copying.txt', 'copying.md'}

@dataclass
class BaseParserService(TreeSitterBase):
    """Base service for parsing files."""
    _language_service: Optional[Any] = None
    
    def __post_init__(self):
        """Initialize the parser service."""
        TreeSitterBase.__post_init__(self)
        from GithubAnalyzer.services.parsers.core.language_service import LanguageService
        if self._language_service is None:
            self._language_service = LanguageService()
        self._log("debug", "Base parser service initialized",
                supported_languages=list(self._language_service.supported_languages))
        
    @timer
    def parse_file(self, file_path: Union[str, Path], language: Optional[str] = None) -> CustomParseResult:
        """Parse a file."""
        file_path = Path(file_path)
        
        # Get language from extension if not provided
        if not language:
            language = self._language_service.get_language_for_file(str(file_path))
        
        # Create FileInfo object
        file_info = FileInfo.from_path(file_path)
        file_info.language = language
        
        # Skip unsupported files
        if not file_info.is_supported:
            self._log("debug", "Skipping unsupported file",
                     file=str(file_path),
                     language=language)
            return CustomParseResult(None, language, is_supported=False)
        
        # Try to read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            self._log("warning", "File appears to be binary",
                     file=str(file_path))
            file_info.is_supported = False
            return CustomParseResult(None, language, is_supported=False)
            
        return self.parse_content(content, language)
        
    @timer
    def parse_content(self, content: str, language: str) -> CustomParseResult:
        """Parse content."""
        try:
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
            
            # Get parser for language
            parser = self._language_service.get_parser(language)
            parser.logger = logger_callback
            
            # Parse content
            tree = parser.parse(bytes(content, "utf8"))
            if tree is None:
                raise ParserError(f"Failed to parse content for language {language}")
            
            # Create basic parse result
            result = CustomParseResult(
                tree=tree,
                language=language,
                metadata={'language': language},
                is_supported=True,
                errors=["Syntax errors detected"] if tree.root_node.has_error else []
            )
            
            self._log("debug", "Content parsed",
                     language=language,
                     has_errors=tree.root_node.has_error)
            
            return result
            
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
        
    def _get_tree_depth(self, node: Tree) -> int:
        """Get the maximum depth of a tree."""
        if not node.children:
            return 0
        return 1 + max(self._get_tree_depth(child) for child in node.children) 