"""Parser service implementation."""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from GithubAnalyzer.services.core.base_service import BaseService
from GithubAnalyzer.models.core.errors import ServiceError, ParserError
from GithubAnalyzer.models.analysis.ast import ParseResult
from GithubAnalyzer.services.core.parsers.base import BaseParser
from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser
from GithubAnalyzer.services.core.parsers.config import ConfigParser
from GithubAnalyzer.services.core.parsers.documentation import DocumentationParser
from GithubAnalyzer.services.core.parsers.license import LicenseParser
from GithubAnalyzer.config.language_config import get_language_by_extension

logger = logging.getLogger(__name__)

class ParserService(BaseService):
    """Service for parsing source code files."""

    # Map file extensions to parser types
    FILE_TYPE_MAPPING = {
        # Source code files
        '.py': 'tree_sitter',
        '.js': 'tree_sitter',
        '.ts': 'tree_sitter',
        '.tsx': 'tree_sitter',
        '.jsx': 'tree_sitter',
        '.java': 'tree_sitter',
        '.cpp': 'tree_sitter',
        '.c': 'tree_sitter',
        '.go': 'tree_sitter',
        
        # Config files
        '.yaml': 'config',
        '.yml': 'config',
        '.json': 'config',
        '.toml': 'config',
        
        # Documentation
        'README.md': 'documentation',
        'LICENSE': 'license',
        '.md': 'documentation',
        '.rst': 'documentation'
    }

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate service configuration.
        
        Args:
            config: Configuration dictionary to validate.
            
        Returns:
            The validated configuration dictionary.
        """
        # No specific config validation needed for parser service
        return config

    def cleanup(self) -> None:
        """Clean up resources."""
        # Clean up parsers
        if hasattr(self, '_parsers'):
            for parser in self._parsers.values():
                if hasattr(parser, 'cleanup'):
                    parser.cleanup()
            self._parsers.clear()

    def initialize(self) -> None:
        """Initialize the service."""
        self._parsers: Dict[str, BaseParser] = {}
        
        # Initialize tree-sitter parser
        self._tree_sitter = TreeSitterParser()  # Store direct reference
        self._tree_sitter.initialize()
        self._parsers['tree_sitter'] = self._tree_sitter
        
        # Initialize other parsers
        self._config_parser = ConfigParser()  # Store direct reference
        self._doc_parser = DocumentationParser()  # Store direct reference
        self._license_parser = LicenseParser()  # Store direct reference
        
        self._parsers['config'] = self._config_parser
        self._parsers['documentation'] = self._doc_parser
        self._parsers['license'] = self._license_parser
        
        self._initialized = True

    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """Parse a source code file."""
        if not self._initialized:
            raise ServiceError("Service not initialized")

        try:
            file_path = Path(file_path)
            parser = self._get_parser_for_file(file_path)
            
            # For tree-sitter parser, determine language from extension
            if isinstance(parser, TreeSitterParser):
                # Remove leading dot and convert to lowercase
                ext = file_path.suffix[1:].lower()
                # Handle special cases
                if ext == 'py':
                    language = 'python'
                elif ext == 'js':
                    language = 'javascript'
                else:
                    language = get_language_by_extension(ext)
                    
                if language is None:
                    raise ServiceError(f"Unsupported file extension: {file_path.suffix}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return parser.parse(content, language)
            
            return parser.parse_file(file_path)
            
        except Exception as e:
            raise ServiceError(f"Failed to parse file: {str(e)}")

    def parse_content(self, content: str, language: str, options: Optional[Dict[str, Any]] = None) -> ParseResult:
        """Parse content directly."""
        if not self._initialized:
            raise ServiceError("Service not initialized")
            
        try:
            parser = self._parsers['tree_sitter']
            if options:
                # Validate options
                valid_options = {'debug', 'include_comments', 'timeout_micros'}
                invalid_options = set(options.keys()) - valid_options
                if invalid_options:
                    raise ValueError(f"Invalid options: {invalid_options}")
                    
                # Apply options to parser
                for key, value in options.items():
                    if key == 'timeout_micros':
                        parser.timeout_micros = value
                    else:
                        setattr(parser, f"_{key}", value)
            try:
                return parser.parse(content, language)
            except KeyError:
                raise ParserError(f"Unsupported language: {language}")
        except Exception as e:
            if isinstance(e, (ValueError, ParserError)):
                raise
            raise ServiceError(f"Failed to parse content: {str(e)}")

    def parse_directory(self, directory: Union[str, Path]) -> List[ParseResult]:
        """Parse all supported files in a directory."""
        if not self._initialized:
            raise ServiceError("Service not initialized")
            
        try:
            directory = Path(directory)
            results = []
            
            for file_path in directory.rglob('*'):
                if file_path.is_file() and (file_path.suffix in self.FILE_TYPE_MAPPING or file_path.name in self.FILE_TYPE_MAPPING):
                    try:
                        result = self.parse_file(file_path)
                        result.file_path = file_path
                        results.append(result)
                    except ServiceError:
                        # Log error but continue parsing
                        logger.warning(f"Failed to parse file: {file_path}")
                        continue
                        
            return results
        except Exception as e:
            raise ServiceError(f"Failed to parse directory: {str(e)}")

    def _get_parser_for_file(self, file_path: Union[str, Path]) -> BaseParser:
        """Get appropriate parser for a file."""
        file_path = Path(file_path)
        
        # Check exact filename matches first
        if file_path.name in self.FILE_TYPE_MAPPING:
            parser_type = self.FILE_TYPE_MAPPING[file_path.name]
            return self._parsers[parser_type]
            
        # Then check file extension
        if file_path.suffix in self.FILE_TYPE_MAPPING:
            parser_type = self.FILE_TYPE_MAPPING[file_path.suffix]
            return self._parsers[parser_type]
            
        raise ParserError(f"No parser found for file: {file_path}")
