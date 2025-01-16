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
        """Parse configuration content."""
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
                }
            )
        except Exception as e:
            raise ParserError(f"Failed to parse config: {str(e)}")

    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """Parse a configuration file."""
        try:
            file_path = Path(file_path)
            content = file_path.read_text(encoding='utf-8')
            
            # Determine format from extension
            format = file_path.suffix[1:].lower()
            if format not in {'yaml', 'yml', 'json', 'toml'}:
                raise ParserError(f"Unsupported config format: {format}")
            
            # Parse content based on format
            if format in {'yaml', 'yml'}:
                import yaml
                data = yaml.safe_load(content)
            elif format == 'json':
                import json
                data = json.loads(content)
            elif format == 'toml':
                import toml
                data = toml.loads(content)
            
            # Create metadata with nested data structure
            metadata = {
                'type': 'config',
                'format': format,
                'data': data  # Keep data nested like in parse()
            }
            
            return ParseResult(
                ast=None,
                language=format,
                is_valid=True,
                line_count=len(content.splitlines()),
                node_count=len(str(data).split()),
                errors=[],
                metadata=metadata
            )
            
        except Exception as e:
            raise ParserError(f"Failed to parse config file: {str(e)}")

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
