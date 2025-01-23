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

# Non-code file extensions
CONFIG_EXTENSIONS = {'yaml', 'yml', 'json'}
DOC_EXTENSIONS = {'md', 'rst', 'txt'}
LICENSE_FILES = {'license', 'license.txt', 'license.md'}

# Language mapping for file extensions
EXTENSION_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.cpp': 'cpp',
    '.c': 'c',
    '.h': 'c',
    '.hpp': 'cpp',
    '.java': 'java',
    '.rb': 'ruby',
    '.go': 'go',
    '.rs': 'rust',
    '.php': 'php',
    '.cs': 'c_sharp',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.m': 'objective-c',
    '.mm': 'objective-cpp'
}

class ParserService:
    """Service for parsing files using tree-sitter."""

    def __init__(self, timeout_micros: Optional[int] = None):
        """Initialize parser service.
        
        Args:
            timeout_micros: Optional timeout in microseconds for parsing operations
        """
        self.timeout_micros = timeout_micros

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect language from file extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            Language identifier or None if not detected
        """
        ext = file_path.suffix.lower()
        return EXTENSION_MAP.get(ext)

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
            
            # Get file extension and content
            content = file_path.read_text()
            
            # Handle non-code files first
            name = file_path.name.lower()
            if name in LICENSE_FILES:
                return ParseResult(tree=None, language='license', content=content, is_code=False)
            
            ext = file_path.suffix.lower().lstrip('.')
            if ext in CONFIG_EXTENSIONS:
                return ParseResult(tree=None, language='config', content=content, is_code=False)
            if ext in DOC_EXTENSIONS:
                return ParseResult(tree=None, language='documentation', content=content, is_code=False)
            
            # Get language and parser
            if not language:
                language = self._detect_language(file_path)
                if not language:
                    raise ParserError(f"Could not detect language for file: {file_path}")
                
            try:
                # Parse code file
                parser = get_parser(language)
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
                raise LanguageError(f"Language not supported: {language}")
            
        except LanguageError:
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
        try:
            try:
                parser = get_parser(language)
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
                raise LanguageError(f"Language not supported: {language}")
            except ParserError:
                raise
            except Exception as e:
                raise ParserError(f"Failed to parse content: {str(e)}")
        except LanguageError:
            raise
        except Exception as e:
            raise ParserError(f"Failed to parse content: {str(e)}")

    def get_required_config_fields(self) -> list[str]:
        """Get required configuration fields."""
        return ["language_bindings"]
