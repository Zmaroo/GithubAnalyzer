"""Service-related error classes."""


class ServiceError(Exception):
    """Base error class for service operations."""


class ServiceNotFoundError(ServiceError):
    """Error raised when a requested service is not found."""


class ServiceNotInitializedError(ServiceError):
    """Error raised when attempting to use an uninitialized service."""


class ServiceAlreadyRegisteredError(ServiceError):
    """Error raised when attempting to register a service that is already registered."""


class ServiceDependencyError(ServiceError):
    """Error raised when a service dependency cannot be satisfied."""


class ServiceInitializationError(ServiceError):
    """Error raised when service initialization fails."""


class ServiceConfigurationError(ServiceError):
    """Error raised when service configuration is invalid."""


class ServiceOperationError(ServiceError):
    """Error raised when a service operation fails."""


class ServiceCleanupError(ServiceError):
    """Error raised when service cleanup fails."""
