"""Exceptions for the GithubAnalyzer package."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class BaseException(Exception):
    """Base class for all GithubAnalyzer exceptions with logging support."""
    message: str
    details: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

    def __str__(self) -> str:
        """Format the exception message."""
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to a dictionary for structured logging."""
        return {
            'type': self.__class__.__name__,
            'message': self.message,
            'details': self.details,
            'context': self.context,
            'correlation_id': self.correlation_id
        }


@dataclass
class DatabaseError(BaseException):
    """Base class for database-related errors."""
    operation: Optional[str] = None
    query: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert database error to a dictionary."""
        data = super().to_dict()
        data.update({
            'operation': self.operation,
            'query': self.query
        })
        return data


@dataclass
class PostgresError(DatabaseError):
    """Error raised when a PostgreSQL operation fails."""
    pass


@dataclass
class Neo4jError(DatabaseError):
    """Error raised when a Neo4j operation fails."""
    pass


@dataclass
class SchemaError(DatabaseError):
    """Error raised when there is a database schema error."""
    schema_file: Optional[str] = None
    line_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema error to a dictionary."""
        data = super().to_dict()
        data.update({
            'schema_file': self.schema_file,
            'line_number': self.line_number
        })
        return data 