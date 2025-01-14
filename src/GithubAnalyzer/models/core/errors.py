"""Core error definitions for the application."""


class BaseError(Exception):
    """Base error class for all application errors."""


class ConfigError(BaseError):
    """Error raised when configuration is invalid."""


class ServiceError(BaseError):
    """Error raised when a service operation fails."""


class ServiceNotFoundError(ServiceError):
    """Error raised when a requested service is not found."""


class ParserError(BaseError):
    """Error raised when parsing operations fail."""


class AnalysisError(BaseError):
    """Error raised when analysis operations fail."""


class StorageError(BaseError):
    """Error raised when storage operations fail."""


class DatabaseError(StorageError):
    """Error raised when database operations fail."""


class ValidationError(BaseError):
    """Error raised when validation fails."""


class UtilityError(BaseError):
    """Error raised when utility operations fail."""


class FrameworkError(BaseError):
    """Error raised when framework-related operations fail."""
