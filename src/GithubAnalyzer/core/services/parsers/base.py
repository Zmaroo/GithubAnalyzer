"""Base parser interface."""

from abc import ABC, abstractmethod
from typing import Optional, List

from ...models.ast import ParseResult
from ...models.errors import ParserError

class BaseParser(ABC):
    """Base class for all parsers."""

    @abstractmethod
    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize parser for specified languages.
        
        Args:
            languages: Optional list of languages to initialize
            
        Raises:
            ParserError: If initialization fails
        """

    @abstractmethod
    def parse(self, content: str, language: str) -> ParseResult:
        """Parse content using specified language.
        
        Args:
            content: Content to parse
            language: Language to use for parsing
            
        Returns:
            ParseResult containing AST and metadata
            
        Raises:
            ParserError: If parsing fails
        """

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up parser resources."""
