"""License parser implementation."""

import logging
from typing import Any, Dict

from ....models.core.errors import ParseError
from .base import BaseParser


class LicenseParser(BaseParser):
    """Parser for license files."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self.logger = logging.getLogger(__name__)
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the parser.

        Raises:
            ParseError: If initialization fails
        """
        try:
            self._initialized = True
            self.logger.info("License parser initialized successfully")
        except Exception as e:
            self.logger.error("Failed to initialize parser: %s", str(e))
            raise ParseError(f"Failed to initialize parser: {str(e)}")

    def parse(self, content: str, language: str = "text") -> Dict[str, Any]:
        """Parse license content.

        Args:
            content: License content to parse
            language: Language to use for parsing (defaults to "text")

        Returns:
            Dict containing license information

        Raises:
            ParseError: If parsing fails
        """
        if not self._initialized:
            raise ParseError("Parser not initialized")

        try:
            # Simple license parsing for now
            return {
                "content": content,
                "type": "unknown",
                "metadata": {"language": language},
            }
        except Exception as e:
            self.logger.error("Failed to parse content: %s", str(e))
            raise ParseError(f"Failed to parse content: {str(e)}")

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a license file.

        Args:
            file_path: Path to license file

        Returns:
            Dict containing license information

        Raises:
            ParseError: If parsing fails
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.parse(content)
        except UnicodeDecodeError:
            raise ParseError(f"File {file_path} is not a text file")
        except Exception as e:
            self.logger.error("Failed to parse file %s: %s", file_path, str(e))
            raise ParseError(f"Failed to parse file {file_path}: {str(e)}")
