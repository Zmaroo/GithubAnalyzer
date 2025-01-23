"""Error classes for the GithubAnalyzer package."""

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ParserError(Exception):
    """Base class for parser-related errors."""
    message: str
    details: Optional[str] = None

@dataclass
class LanguageError(ParserError):
    """Error raised when a language is not supported."""
    pass

@dataclass
class QueryError(ParserError):
    """Error raised when a query fails."""
    pass

@dataclass
class FileOperationError(Exception):
    """Error raised when a file operation fails."""
    message: str
    details: Optional[str] = None

@dataclass
class ConfigError(Exception):
    """Error raised when there is a configuration error."""
    message: str
    details: Optional[str] = None

@dataclass
class ServiceError(Exception):
    """Error raised when a service operation fails."""
    message: str
    details: Optional[str] = None

__all__ = [
    "ParserError",
    "LanguageError",
    "QueryError",
    "FileOperationError",
    "ConfigError",
    "ServiceError",
]
