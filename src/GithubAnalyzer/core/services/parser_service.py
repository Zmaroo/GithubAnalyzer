"""Parser service for orchestrating code analysis."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from ...models.core.ast import ParseResult
from ...models.core.errors import ParserError, ServiceError
from ...models.core.file import FileInfo, FileType
from .parsers.base import BaseParser
from .parsers.config_parser import ConfigParser
from ..common.cache_service import CacheService
from ...utils.context_manager import ContextManager
from ...utils.logging import StructuredLogger
from .base_service import BaseService


class ParserService(BaseService):
    """Service for orchestrating parsing operations."""

    def __init__(
        self,
        cache_service: Optional[CacheService] = None,
        context_manager: Optional[ContextManager] = None
    ):
        """Initialize parser service.
        
        Args:
            cache_service: Optional cache service instance
            context_manager: Optional context manager instance
        """
        super().__init__()
        self._cache = cache_service or CacheService()
        self._context = context_manager or ContextManager()
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
                self._cache.initialize(["ast"])
                
                # Initialize config parser by default
                if not parser_types or "config" in parser_types:
                    config_parser = ConfigParser(cache_service=self._cache)
                    config_parser.initialize()
                    self._parsers["config"] = config_parser
                        
                self._initialized = True
                self.logger.info("Parser service initialized", parser_types=parser_types)
        except Exception as e:
            raise ServiceError(f"Failed to initialize parser service: {str(e)}")

    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """Parse a file using appropriate parser.
        
        Args:
            file_path: Path to file to parse
            
        Returns:
            ParseResult containing AST and metadata
            
        Raises:
            ParserError: If parsing fails
            ServiceError: If service not initialized
        """
        self._ensure_initialized()
        
        try:
            file_path = Path(file_path)
            cache_key = str(file_path.resolve())
            
            # Check cache first
            cached_result = self._cache.get("ast", cache_key)
            if cached_result:
                return cached_result
            
            # Get appropriate parser
            parser = self._get_parser_for_file(file_path)
            if not parser:
                raise ParserError(f"No parser available for file: {file_path}")
            
            # Parse file
            result = parser.parse_file(file_path)
            
            # Cache result
            self._cache.set("ast", cache_key, result)
            
            return result
            
        except Exception as e:
            raise ParserError(f"Failed to parse file: {str(e)}")

    def cleanup(self) -> None:
        """Clean up service resources."""
        for parser in self._parsers.values():
            parser.cleanup()
        self._parsers.clear()
        self._cache.cleanup()
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
