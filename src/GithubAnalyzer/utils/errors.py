"""Utility error classes."""


class UtilityError(Exception):
    """Base error class for utility operations."""


class ConfigError(UtilityError):
    """Error raised when configuration is invalid."""


class ValidationError(UtilityError):
    """Error raised when validation fails."""


class FileError(UtilityError):
    """Error raised when file operations fail."""


class PerformanceError(UtilityError):
    """Error raised when performance thresholds are exceeded."""


class LoggingError(UtilityError):
    """Error raised when logging operations fail."""


class ContainerError(UtilityError):
    """Error raised when container operations fail."""
