from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

"""Error classes for the GithubAnalyzer package."""

from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class BaseError(Exception):
    """Base error class."""
    message: str
    details: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        """Get string representation of error."""
        if self.details:
            return f"{self.message} - {self.details}"
        return self.message

@dataclass
class EditorError(BaseError):
    """Error related to editor operations."""
    pass

@dataclass
class LanguageError(BaseError):
    """Error related to language operations."""
    pass

@dataclass
class ParserError(BaseError):
    """Error related to parsing operations."""
    pass

@dataclass
class TraversalError(BaseError):
    """Error related to AST traversal."""
    pass

@dataclass
class ValidationError(BaseError):
    """Error related to validation."""
    pass

@dataclass
class DatabaseError(BaseError):
    """Error related to database operations."""
    pass

@dataclass
class ServiceError(BaseError):
    """Error related to service operations."""
    pass

@dataclass
class ConfigError(BaseError):
    """Error related to configuration."""
    pass

@dataclass
class AnalysisError(BaseError):
    """Error related to code analysis."""
    pass

@dataclass
class QueryError(BaseError):
    """Error related to query operations."""
    pass

@dataclass
class PatternError(BaseError):
    """Error related to pattern operations."""
    pass

@dataclass
class FileError(BaseError):
    """Error related to file operations."""
    pass

@dataclass
class GraphError(BaseError):
    """Error related to graph operations."""
    pass

@dataclass
class CacheError(BaseError):
    """Error related to caching operations."""
    pass

@dataclass
class AuthError(BaseError):
    """Error related to authentication."""
    pass

@dataclass
class APIError(BaseError):
    """Error related to API operations."""
    pass

@dataclass
class NetworkError(BaseError):
    """Error related to network operations."""
    pass

@dataclass
class TimeoutError(BaseError):
    """Error related to timeouts."""
    pass

@dataclass
class ResourceError(BaseError):
    """Error related to resource management."""
    pass

@dataclass
class StateError(BaseError):
    """Error related to state management."""
    pass

@dataclass
class RepositoryError(BaseError):
    """Error related to repository operations."""
    pass

__all__ = [
    'BaseError',
    'EditorError',
    'LanguageError',
    'ParserError',
    'TraversalError',
    'ValidationError',
    'DatabaseError',
    'RepositoryError',
    'ServiceError',
    'ConfigError',
    'AnalysisError',
    'QueryError',
    'PatternError',
    'FileError',
    'GraphError',
    'CacheError',
    'AuthError',
    'APIError',
    'NetworkError',
    'TimeoutError',
    'ResourceError',
    'StateError'
] 