"""Parser service for code analysis using tree-sitter."""
import os
from pathlib import Path
from typing import Union, Optional, Callable, Dict, Any, Set
from tree_sitter import Tree, Language, Parser
from tree_sitter_language_pack import get_parser, get_language
import logging

from GithubAnalyzer.models.core.errors import ParserError, LanguageError
from GithubAnalyzer.utils.timing import timer
from GithubAnalyzer.models.core.ast import ParseResult
from GithubAnalyzer.models.core.file import FileInfo
from GithubAnalyzer.utils.logging import get_logger
from GithubAnalyzer.services.analysis.parsers.tree_sitter_query import TreeSitterQueryHandler
from GithubAnalyzer.services.analysis.parsers.language_service import LanguageService

logger = get_logger(__name__)

# Special file types that don't need parsing
LICENSE_FILES = {'license', 'license.txt', 'license.md', 'copying', 'copying.txt', 'copying.md'}

# Map file extensions to tree-sitter language names
EXTENSION_MAP = {
    # C family
    '.c': 'c',
    '.h': 'c',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.c++': 'cpp',
    
    # Web
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.html': 'html',
    '.css': 'css',
    '.php': 'php',
    
    # System
    '.sh': 'bash',
    '.bash': 'bash',
    '.rs': 'rust',
    '.go': 'go',
    '.java': 'java',
    '.scala': 'scala',
    '.rb': 'ruby',
    '.py': 'python',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.kts': 'kotlin',
    
    # Data/Config
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.toml': 'toml',
    '.xml': 'xml',
    
    # Documentation
    '.md': 'markdown',
    '.rst': 'rst',
    '.org': 'org',
    
    # Other languages
    '.lua': 'lua',
    '.r': 'r',
    '.elm': 'elm',
    '.ex': 'elixir',
    '.exs': 'elixir',
    '.erl': 'erlang',
    '.hrl': 'erlang',
    '.hs': 'haskell',
    '.lhs': 'haskell',
    '.pl': 'perl',
    '.pm': 'perl',
    '.sql': 'sql',
    '.vue': 'vue',
    '.zig': 'zig'
}

class ParserService:
    """Service for parsing files using tree-sitter."""

    def __init__(self):
        """Initialize the parser service."""
        self._language_service = LanguageService()
        self._query_handler = TreeSitterQueryHandler()
        
    @timer
    def parse_file(self, file_path: Union[str, Path], language: Optional[str] = None) -> ParseResult:
        """Parse a file using tree-sitter.
        
        Args:
            file_path: Path to the file to parse
            language: Optional language identifier (will be detected from extension if not provided)
            
        Returns:
            ParseResult containing the tree and metadata
        """
        file_path = Path(file_path)
        
        # Skip license files
        if file_path.name.lower() in LICENSE_FILES:
            return ParseResult(None, None, FileInfo(file_path, is_binary=False))
        
        # Get language from extension if not provided
        if not language:
            language = self._language_service.get_language_for_file(str(file_path))
            if not language:
                logger.warning(f"Unsupported file type: {file_path.suffix}")
                return ParseResult(None, None, FileInfo(file_path, is_unsupported=True))
            
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"File {file_path} appears to be binary")
            return ParseResult(None, None, FileInfo(file_path, is_binary=True))
            
        return self.parse_content(content, language)
        
    @timer
    def parse_content(self, content: str, language: str) -> ParseResult:
        """Parse content using tree-sitter.
        
        Args:
            content: Content to parse
            language: Language identifier
            
        Returns:
            ParseResult containing the tree and metadata
        """
        try:
            # Get parser for language
            parser = self._language_service.get_parser(language)
            
            # Parse content
            tree = parser.parse(bytes(content, 'utf-8'))
            
            # Validate syntax using query handler
            is_valid, errors = self._query_handler.validate_syntax(tree.root_node, language)
            
            # Extract functions and other structures
            functions = self._query_handler.find_functions(tree.root_node, language)
            classes = self._query_handler.find_nodes(tree, "class", language)
            imports = self._query_handler.find_nodes(tree, "import", language)
            
            # Get any missing or error nodes
            missing_nodes = self._query_handler.find_missing_nodes(tree.root_node)
            error_nodes = self._query_handler.find_error_nodes(tree.root_node)
            
            return ParseResult(
                tree=tree,
                language=language,
                functions=functions,
                classes=classes,
                imports=imports,
                is_valid=is_valid,
                errors=errors,
                missing_nodes=missing_nodes,
                error_nodes=error_nodes
            )
            
        except Exception as e:
            logger.error(f"Failed to parse content: {str(e)}")
            raise ParserError(f"Failed to parse content: {str(e)}")
            
    def get_supported_languages(self) -> Set[str]:
        """Get set of supported languages."""
        return self._language_service.supported_languages
