"""Parser service for orchestrating code analysis."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from src.GithubAnalyzer.core.models.ast import ParseResult
from src.GithubAnalyzer.core.models.errors import ParserError, ServiceError, ConfigError
from src.GithubAnalyzer.core.models.file import FileInfo, FileType
from src.GithubAnalyzer.core.services.parsers.base import BaseParser
from src.GithubAnalyzer.core.services.parsers.config_parser import ConfigParser
from src.GithubAnalyzer.common.services.cache_service import CacheService
from src.GithubAnalyzer.core.utils.context_manager import ContextManager
from src.GithubAnalyzer.core.utils.logging import StructuredLogger
from src.GithubAnalyzer.core.services.base_service import BaseService


class ParserService(BaseService):
    """Service for orchestrating parsing operations."""

    def __init__(self, cache_service=None):
        """Initialize parser service."""
        super().__init__()
        self.cache_service = cache_service or CacheService()
        self._context = ContextManager()
        self._parsers: Dict[str, BaseParser] = {}
        self.logger = StructuredLogger(__name__)
        self._initialized = False

    def register_parser(self, name: str, parser: BaseParser) -> None:
        """Register a parser implementation.
        
        Args:
            name: Name/type of the parser
            parser: Parser instance to register
            
        Raises:
            ServiceError: If parser is already registered
        """
        if name in self._parsers:
            raise ServiceError(f"Parser {name} already registered")
        self._parsers[name] = parser
        self.logger.info(f"Registered parser", parser_name=name)

    def initialize(self, parser_types: Optional[List[str]] = None) -> None:
        """Initialize parser service.
        
        Args:
            parser_types: Optional list of parser types to initialize
            
        Raises:
            ServiceError: If initialization fails
        """
        try:
            if not self._initialized:
                self._context.start()
                self.cache_service.initialize(["ast"])
                
                # Only initialize config parser if needed
                if not parser_types or "config" in parser_types:
                    try:
                        config_parser = ConfigParser(cache_service=self.cache_service)
                        config_parser.initialize()
                        self._parsers["config"] = config_parser
                    except Exception as e:
                        self.logger.warning(f"Failed to initialize config parser: {e}")
                        
                self._initialized = True
                self.logger.info("Parser service initialized", parser_types=parser_types)
        except Exception as e:
            raise ServiceError(f"Failed to initialize parser service: {str(e)}")

    def parse_file(self, file_info: Union[str, Path, FileInfo]) -> ParseResult:
        """Parse a file using appropriate parser.
        
        Args:
            file_info: Path or FileInfo object for the file to parse
            
        Returns:
            ParseResult containing AST and metadata
            
        Raises:
            ParserError: If parsing fails
            ServiceError: If service not initialized
        """
        self._ensure_initialized()
        
        try:
            # Handle FileInfo objects
            if isinstance(file_info, FileInfo):
                file_path = file_info.path
            else:
                file_path = Path(file_info)
            
            cache_key = str(file_path.resolve())
            
            # Check cache first
            cached_result = self.cache_service.get("ast", cache_key)
            if cached_result:
                return cached_result
            
            # Get appropriate parser
            parser = self._get_parser_for_file(file_path)
            if not parser:
                raise ParserError(f"No parser available for file: {file_path}")
            
            # Parse file
            result = parser.parse_file(file_path)
            
            # Cache result
            self.cache_service.set("ast", cache_key, result)
            
            return result
            
        except Exception as e:
            raise ParserError(f"Failed to parse file: {str(e)}")

    def cleanup(self) -> None:
        """Clean up service resources."""
        for parser in self._parsers.values():
            parser.cleanup()
        self._parsers.clear()
        self.cache_service.cleanup()
        self._context.stop()
        self._initialized = False
        self.logger.info("Parser service cleaned up")

    def _get_parser_for_file(self, file_path: Path) -> Optional[BaseParser]:
        """Get appropriate parser for file type."""
        # Get file extension
        ext = file_path.suffix.lower().lstrip('.')
        
        # Config files
        if ext in ['yaml', 'yml', 'json']:
            return self._parsers.get('config')
            
        # Documentation files
        if ext in ['md', 'rst', 'txt']:
            return self._parsers.get('documentation')
            
        # License files
        if file_path.name.lower() in ['license', 'license.txt', 'license.md']:
            return self._parsers.get('license')
            
        # Default to tree-sitter for code files
        return self._parsers.get('tree-sitter')

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parser service configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Validated configuration
            
        Raises:
            ConfigError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ConfigError("Configuration must be a dictionary")
        return config

    def _ensure_initialized(self) -> None:
        """Ensure service is initialized."""
        if not self._initialized:
            raise ServiceError("Parser service not initialized")

    def parse_content(self, content: str, language: str) -> ParseResult:
        """Parse content string.
        
        Args:
            content: Content to parse
            language: Language identifier
            
        Returns:
            ParseResult containing AST and metadata
            
        Raises:
            ParserError: If parsing fails
            ServiceError: If service not initialized
        """
        self._ensure_initialized()
        
        try:
            parser = self._parsers.get(language)
            if not parser:
                raise ParserError(f"No parser available for language: {language}")
                
            return parser.parse(content, language)
            
        except Exception as e:
            raise ParserError(f"Failed to parse content: {str(e)}")
