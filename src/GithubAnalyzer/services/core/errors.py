"""Core service errors."""


class ServiceError(Exception):
    """Base class for service errors."""

    pass


class ConfigError(ServiceError):
    """Configuration error."""

    pass


class DatabaseError(ServiceError):
    """Database error."""

    pass


class ParseError(ServiceError):
    """Parse error."""

    pass


class FrameworkError(ServiceError):
    """Framework error."""

    pass


class GraphError(ServiceError):
    """Graph error."""

    pass
