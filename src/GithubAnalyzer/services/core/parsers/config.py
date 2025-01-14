"""Configuration parser implementation."""

from typing import Any, Dict

import yaml

from ....models.core.errors import ParseError
from ....models.core.parse import ParseResult
from .base import BaseParser


class ConfigParser(BaseParser):
    """Parser for configuration files."""

    def _validate_config(self) -> None:
        """Validate parser configuration."""
        # No specific config needed for config parsing
        pass

    def parse(self, content: str) -> ParseResult:
        """Parse configuration content.

        Args:
            content: Configuration content to parse

        Returns:
            ParseResult containing parsed configuration

        Raises:
            ParseError: If parsing fails
        """
        try:
            config_data = yaml.safe_load(content)
            if not isinstance(config_data, dict):
                raise ParseError("Configuration must be a dictionary")

            return ParseResult(
                content=content,
                ast=config_data,
                line_count=len(content.splitlines()),
                char_count=len(content),
                metadata={
                    "type": "configuration",
                    "format": "yaml",
                    "keys": list(config_data.keys()),
                },
            )
        except yaml.YAMLError as e:
            raise ParseError(f"Failed to parse YAML configuration: {str(e)}")
        except Exception as e:
            raise ParseError(f"Failed to parse configuration: {str(e)}")
