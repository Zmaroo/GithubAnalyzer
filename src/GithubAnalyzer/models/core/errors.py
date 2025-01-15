"""Core error definitions."""

class BaseError(Exception):
    """Base error class for all custom exceptions."""


class ServiceError(BaseError):
    """Error raised by services."""


class ParserError(ServiceError):
    """Error raised by parsers."""


class ConfigError(ServiceError):
    """Error raised during configuration."""


class DatabaseError(ServiceError):
    """Error raised by database operations."""


class FileOperationError(BaseError):
    """Error raised during file operations."""


class FrameworkError(BaseError):
    """Error raised by framework components."""


class ServiceNotFoundError(FrameworkError):
    """Error raised when a required service is not found."""


__all__ = [
    "BaseError",
    "ServiceError",
    "ParserError",
    "ConfigError",
    "DatabaseError",
    "FileOperationError",
    "FrameworkError",
    "ServiceNotFoundError",
]
