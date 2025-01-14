"""Parser service implementation."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, cast

from ...config.language_config import get_file_type_mapping, get_language_by_extension
from ...models.analysis.ast import ParseResult
from ...models.core.errors import ServiceError
from ..base import BaseService
from .parsers.base import BaseParser
from .parsers.config import ConfigParser
from .parsers.documentation import DocumentationParser
from .parsers.license import LicenseParser
from .parsers.tree_sitter import TreeSitterParser


class ParserService(BaseService):
    """Service for parsing code and files."""

    SUPPORTED_PARSERS = {
        "tree-sitter": TreeSitterParser,
        "config": ConfigParser,
        "documentation": DocumentationParser,
        "license": LicenseParser,
    }

    # File type mapping is now loaded from language_config
    FILE_TYPE_MAPPING = get_file_type_mapping()

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the parser service.

        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(config or {})
        self._parsers: Dict[str, BaseParser] = {}
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

        # Default to tree-sitter if no parser type specified
        if "parser_type" not in config:
            config["parser_type"] = "tree-sitter"

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
            # Initialize all parsers
            for parser_type, parser_class in self.SUPPORTED_PARSERS.items():
                self._parsers[parser_type] = parser_class()
                if parser_type == "tree-sitter":
                    # Only tree-sitter needs language initialization
                    self._parsers[parser_type].initialize(languages)
                else:
                    self._parsers[parser_type].initialize()

            self._initialized = True
        except Exception as e:
            raise ServiceError(f"Failed to initialize parsers: {str(e)}")

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

        # Default to tree-sitter
        return self._parsers["tree-sitter"]

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

        # Try tree-sitter first for code parsing
        try:
            result = self._parsers["tree-sitter"].parse(content, language)
            if not isinstance(result, ParseResult):
                raise ServiceError("Parser returned invalid result type")
            return result
        except Exception as e:
            # If tree-sitter fails, try other parsers based on content
            for parser_type, parser in self._parsers.items():
                if parser_type != "tree-sitter":
                    try:
                        result = parser.parse(content, language)
                        if not isinstance(result, ParseResult):
                            continue
                        return result
                    except:
                        continue

            # If all parsers fail, raise the original error
            raise ServiceError(f"Failed to parse content: {str(e)}")

    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
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
            file_path = Path(file_path)
            parser = self._get_parser_for_file(file_path)

            # For tree-sitter parser, determine language from extension
            if isinstance(parser, TreeSitterParser):
                language = get_language_by_extension(file_path.suffix)
                if language is None:
                    raise ServiceError(
                        f"Unsupported file extension: {file_path.suffix}"
                    )
                result = parser.parse_file(file_path)
                if not isinstance(result, ParseResult):
                    raise ServiceError("Parser returned invalid result type")
                return result

            result = parser.parse_file(file_path)
            if not isinstance(result, ParseResult):
                raise ServiceError("Parser returned invalid result type")
            return result
        except Exception as e:
            raise ServiceError(f"Failed to parse file: {str(e)}")

    def cleanup(self) -> None:
        """Clean up parser resources."""
        for parser in self._parsers.values():
            parser.cleanup()
        self._initialized = False
        self._parsers.clear()

    @property
    def initialized(self) -> bool:
        """Check if the service is initialized.

        Returns:
            True if initialized, False otherwise.
        """
        return self._initialized
