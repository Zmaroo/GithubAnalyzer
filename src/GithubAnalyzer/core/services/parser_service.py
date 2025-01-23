"""Parser service for code analysis using tree-sitter."""

from pathlib import Path
from typing import Union, Optional
import logging
from tree_sitter_language_pack import get_parser, get_language

from src.GithubAnalyzer.core.models.ast import ParseResult
from src.GithubAnalyzer.core.models.errors import ParserError, LanguageError
from src.GithubAnalyzer.core.models.file import FileInfo
from src.GithubAnalyzer.core.utils.timing import timer

logger = logging.getLogger(__name__)

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
    '.cs': 'c-sharp',
    
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
    '.txt': 'text',
    '.rst': 'rst',
    '.org': 'org',
    '.ini': 'ini',
    
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
    '.ml': 'ocaml',
    '.mli': 'ocaml',
    '.pl': 'perl',
    '.pm': 'perl',
    '.proto': 'protobuf',
    '.sql': 'sql',
    '.vue': 'vue',
    '.zig': 'zig'
}

class ParserService:
    """Service for parsing files using tree-sitter."""

    def __init__(self, timeout_micros: Optional[int] = None):
        """Initialize parser service.
        
        Args:
            timeout_micros: Optional timeout in microseconds for parsing operations
        """
        self.timeout_micros = timeout_micros

    def _detect_language(self, file_path: Path) -> str:
        """Detect language from file extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            Language identifier based on file extension
        """
        ext = file_path.suffix.lower()
        return EXTENSION_MAP.get(ext, ext.lstrip('.'))

    def _parse_code(self, content: str, language: str) -> ParseResult:
        """Parse code content using tree-sitter.
        
        Args:
            content: Content to parse
            language: Language identifier
            
        Returns:
            ParseResult containing tree-sitter Tree
            
        Raises:
            ParserError: If parsing fails
            LanguageError: If language is not supported
        """
        try:
            parser = get_parser(language)
            # Set parser logger to debug level
            parser.logger = logger.debug
            if self.timeout_micros is not None:
                parser.timeout_micros = self.timeout_micros
            tree = parser.parse(bytes(content, "utf8"))
            
            # Check for syntax errors
            if tree.root_node.has_error:
                error_nodes = [
                    node for node in tree.root_node.children 
                    if node.has_error or node.type == 'ERROR'
                ]
                if error_nodes:
                    error_msg = "Syntax errors found:\n"
                    for node in error_nodes:
                        error_msg += f"- ERROR at line {node.start_point[0] + 1}: {node.type}\n"
                    raise ParserError(error_msg)
            
            return ParseResult(
                tree=tree,
                language=language,
                content=content,
                is_code=True
            )
        except LookupError:
            raise LanguageError(f"Language not supported by tree-sitter: {language}")
        except ParserError:
            raise
        except Exception as e:
            raise ParserError(f"Failed to parse content: {str(e)}")

    @timer
    def parse_file(self, file_info: Union[str, Path, FileInfo]) -> ParseResult:
        """Parse a file using tree-sitter or return raw content for non-code files.
        
        Args:
            file_info: Path or FileInfo object for the file to parse
            
        Returns:
            ParseResult containing tree-sitter Tree for code files or raw content for others
            
        Raises:
            ParserError: If parsing fails
            LanguageError: If language is not supported
        """
        try:
            # Handle FileInfo objects
            if isinstance(file_info, FileInfo):
                file_path = file_info.path
                language = file_info.language
            else:
                file_path = Path(file_info)
                language = None
            
            # Get file content
            content = file_path.read_text()
            
            # Handle license files
            name = file_path.name.lower()
            if name in LICENSE_FILES:
                return ParseResult(tree=None, language='license', content=content, is_code=False)
            
            # Get language and try to parse
            if not language:
                language = self._detect_language(file_path)
            
            # Special handling for known non-code files
            if language in {'rst', 'org', 'ini'}:
                return ParseResult(tree=None, language='documentation', content=content, is_code=False)
            
            try:
                return self._parse_code(content, language)
            except LanguageError:
                # If parsing fails due to unsupported language, treat as non-code file
                logger.info(f"File {file_path} has unsupported language: {language}")
                return ParseResult(tree=None, language='unknown', content=content, is_code=False)
            
        except (ParserError):
            raise
        except Exception as e:
            raise ParserError(f"Failed to parse file: {str(e)}")

    @timer
    def parse_content(self, content: str, language: str) -> ParseResult:
        """Parse content string using tree-sitter.
        
        Args:
            content: Content to parse
            language: Language identifier
            
        Returns:
            ParseResult containing tree-sitter Tree
            
        Raises:
            ParserError: If parsing fails
            LanguageError: If language is not supported
        """
        return self._parse_code(content, language)
