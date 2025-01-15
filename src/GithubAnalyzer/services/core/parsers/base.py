"""Base parser interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from GithubAnalyzer.models.analysis.ast import ParseResult
from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.services.core.base_service import BaseService


class BaseParser(ABC):
    """Base class for all parsers."""

    @abstractmethod
    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize the parser.

        Args:
            languages: Optional list of languages to initialize support for

        Raises:
            ParserError: If initialization fails
        """

    @abstractmethod
    def parse(self, content: str, language: str) -> ParseResult:
        """Parse content.

        Args:
            content: Content to parse
            language: Language identifier for the content

        Returns:
            ParseResult containing AST and metadata

        Raises:
            ParserError: If parsing fails
        """

    @abstractmethod
    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """Parse a file.

        Args:
            file_path: Path to the file to parse

        Returns:
            ParseResult containing AST and metadata

        Raises:
            ParserError: If parsing fails
        """

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up parser resources."""
