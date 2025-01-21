"""Configuration file parser implementation."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ...models.ast import ParseResult
from ...models.errors import ParserError
from ...models.file import FileInfo, FileType
from ...config.parser_config import CONFIG_FILE_FORMATS, get_config_format
from .base import BaseParser
from ....common.services.cache_service import CacheService
from ...utils.context_manager import ContextManager
from ...utils.decorators import retry, timeout, timer


class ConfigParser(BaseParser):
    """Parser for configuration files (YAML, JSON, TOML, etc.)."""

    def __init__(self, cache_service=None):
        """Initialize config parser.
        
        Args:
            cache_service: Optional cache service instance
        """
        super().__init__()
        self.cache_service = cache_service

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
            content: The configuration content to parse
            language: The configuration format (yaml, json, etc.)
            
        Returns:
            ParseResult containing the parsed configuration
            
        Raises:
            ParserError: If parsing fails or format not supported
        """
        try:
            if language not in CONFIG_FILE_FORMATS:
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
                    "mime_type": CONFIG_FILE_FORMATS[language]["mime_types"][0]
                }
            )
        except Exception as e:
            raise ParserError(f"Failed to parse config: {str(e)}")

    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """Parse a configuration file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            ParseResult containing the parsed configuration
            
        Raises:
            ParserError: If parsing fails or format not supported
        """
        try:
            file_path = Path(file_path)
            content = file_path.read_text(encoding='utf-8')
            
            # Use parser_config to determine format
            format = get_config_format(str(file_path))
            if not format:
                raise ParserError(f"Unsupported config format for file: {file_path}")
            
            return self.parse(content, format)
            
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