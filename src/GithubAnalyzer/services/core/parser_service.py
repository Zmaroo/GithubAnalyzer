"""Parser service implementation."""

from typing import Any, Dict, List, Optional, Type

from ...models.core.errors import ServiceError
from ...models.core.parse import ParseResult
from .base_service import BaseService
from .parsers.base import BaseParser
from .parsers.tree_sitter import TreeSitterParser


class ParserService(BaseService):
    """Service for parsing code and files."""

    SUPPORTED_PARSERS = {"tree-sitter": TreeSitterParser}

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the parser service.

        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(config)
        self._parser: Optional[BaseParser] = None
        self._initialized = False

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the service configuration.

        Args:
            config: Configuration dictionary to validate.

        Returns:
            The validated configuration dictionary.

        Raises:
            ServiceError: If the configuration is invalid.
        """
        if not isinstance(config, dict):
            raise ServiceError("Configuration must be a dictionary")

        if "parser_type" not in config:
            raise ServiceError("Missing required config key: parser_type")

        parser_type = config["parser_type"]
        if parser_type not in self.SUPPORTED_PARSERS:
            raise ServiceError(f"Unsupported parser type: {parser_type}")

        return config

    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize the parser service.

        Args:
            languages: Optional list of languages to initialize parsers for.

        Raises:
            ServiceError: If initialization fails.
        """
        if not self._config:
            raise ServiceError("Configuration is required")

        try:
            self._parser = self._create_parser()
            self._parser.initialize(languages)
            self._initialized = True
        except Exception as e:
            raise ServiceError(f"Failed to initialize parser: {str(e)}")

    def _create_parser(self) -> BaseParser:
        """Create a parser instance based on the configuration.

        Returns:
            The created parser instance.

        Raises:
            ServiceError: If parser creation fails.
        """
        parser_type = self._config.get("parser_type")
        if not parser_type:
            raise ServiceError("Parser type not specified")

        parser_class = self.SUPPORTED_PARSERS.get(parser_type)
        if not parser_class:
            raise ServiceError(f"Unsupported parser type: {parser_type}")

        try:
            return parser_class()
        except Exception as e:
            raise ServiceError(f"Failed to create parser: {str(e)}")

    def parse(self, content: str, language: str) -> ParseResult:
        """Parse code content.

        Args:
            content: Source code content to parse.
            language: Programming language of the content.

        Returns:
            ParseResult containing the parsed AST and metadata.

        Raises:
            ServiceError: If parsing fails.
        """
        if not self._initialized:
            raise ServiceError("Service not initialized")

        try:
            return self._parser.parse(content, language)
        except Exception as e:
            raise ServiceError(f"Failed to parse content: {str(e)}")

    def parse_file(self, file_path: str) -> ParseResult:
        """Parse a source code file.

        Args:
            file_path: Path to the source code file.

        Returns:
            ParseResult containing the parsed AST and metadata.

        Raises:
            ServiceError: If parsing fails.
        """
        if not self._initialized:
            raise ServiceError("Service not initialized")

        try:
            return self._parser.parse_file(file_path)
        except Exception as e:
            raise ServiceError(f"Failed to parse file: {str(e)}")

    def cleanup(self) -> None:
        """Clean up parser resources."""
        if self._parser:
            self._parser.cleanup()
        self._initialized = False
        self._parser = None

    @property
    def initialized(self) -> bool:
        """Check if the service is initialized.

        Returns:
            True if initialized, False otherwise.
        """
        return self._initialized
