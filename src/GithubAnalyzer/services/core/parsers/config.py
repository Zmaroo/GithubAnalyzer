"""Configuration file parser implementation."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ....models.analysis.ast import ParseResult
from ....models.core.errors import ParserError
from .base import BaseParser


class ConfigParser(BaseParser):
    """Parser for configuration files."""

    SUPPORTED_FORMATS = {
        "yaml": [".yaml", ".yml"],
        "json": [".json"],
        "toml": [".toml"],
        "ini": [".ini"],
    }

    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize the parser.

        Args:
            languages: Optional list of languages to initialize support for

        Raises:
            ParserError: If initialization fails
        """
        # No specific initialization needed for config parsing
        pass

    def parse(self, content: str, language: str) -> ParseResult:
        """Parse configuration content.

        Args:
            content: Content to parse
            language: Language identifier for the content

        Returns:
            ParseResult containing configuration information

        Raises:
            ParserError: If parsing fails
        """
        try:
            if language not in self.SUPPORTED_FORMATS:
                raise ParserError(f"Unsupported config format: {language}")

            # Parse based on format
            if language in ["yaml", "yml"]:
                data = yaml.safe_load(content)
            elif language == "json":
                data = json.loads(content)
            else:
                raise ParserError(f"Parser for {language} not implemented")

            return ParseResult(
                ast=None,  # Config parser doesn't produce an AST
                language=language,
                is_valid=True,
                line_count=len(content.splitlines()),
                node_count=self._count_nodes(data),
                errors=[],
                metadata={
                    "type": "config",
                    "format": language,
                    "data": data,
                },
            )
        except Exception as e:
            raise ParserError(f"Failed to parse config: {str(e)}")

    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """Parse a configuration file.

        Args:
            file_path: Path to the file to parse

        Returns:
            ParseResult containing configuration information

        Raises:
            ParserError: If file cannot be read or parsed
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise ParserError(f"File {file_path} not found")

        # Determine format from extension
        ext = file_path.suffix.lower()
        language = None
        for fmt, exts in self.SUPPORTED_FORMATS.items():
            if ext in exts:
                language = fmt
                break

        if language is None:
            raise ParserError(f"Unsupported config format: {ext}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            result = self.parse(content, language)
            result.metadata["file_path"] = str(file_path)
            return result
        except Exception as e:
            raise ParserError(f"Failed to parse file {file_path}: {str(e)}")

    def cleanup(self) -> None:
        """Clean up parser resources."""
        # No cleanup needed for config parser
        pass

    def _count_nodes(self, data: Any) -> int:
        """Count nodes in parsed data recursively."""
        if isinstance(data, (dict, list)):
            count = 1  # Count current container
            if isinstance(data, dict):
                for key, value in data.items():
                    count += self._count_nodes(value)
            else:  # list
                for item in data:
                    count += self._count_nodes(item)
            return count
        return 1  # Count leaf nodes
