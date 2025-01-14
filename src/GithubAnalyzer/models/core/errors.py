"""Core error definitions"""


class BaseError(Exception):
    """Base error class for all custom exceptions."""


class ConfigError(BaseError):
    """Error raised when configuration is invalid."""


class DatabaseError(BaseError):
    """Error raised when database operations fail."""


class ParseError(BaseError):
    """Error raised when parsing operations fail."""


class FrameworkError(BaseError):
    """Error raised when framework operations fail."""


class ServiceError(BaseError):
    """Error raised when service operations fail."""


class ServiceNotFoundError(ServiceError):
    """Error raised when a requested service is not found."""


class ValidationError(BaseError):
    """Error raised when validation fails."""


class AnalysisError(BaseError):
    """Error raised when analysis operations fail."""
