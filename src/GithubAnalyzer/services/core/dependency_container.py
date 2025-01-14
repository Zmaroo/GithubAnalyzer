"""Dependency injection container."""

from typing import Any, Dict, Optional, Type, TypeVar

from GithubAnalyzer.models.core.errors import ServiceError

from .base_service import BaseService

T = TypeVar("T", bound=BaseService)


class DependencyContainer:
    """Container for managing service dependencies."""

    def __init__(self) -> None:
        """Initialize the container."""
        self._services: Dict[str, BaseService] = {}
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Check if container is initialized."""
        return self._initialized

    def register_service(self, service_type: Type[T], service: T) -> None:
        """Register a service.

        Args:
            service_type: Type of service to register
            service: Service instance

        Raises:
            ServiceError: If service registration fails
        """
        if not isinstance(service, service_type):
            raise ServiceError(
                f"Service must be an instance of {service_type.__name__}"
            )

        service_name = service_type.__name__
        if service_name in self._services:
            raise ServiceError(f"Service {service_name} already registered")

        self._services[service_name] = service

    def get_service(self, service_type: Type[T]) -> T:
        """Get a registered service.

        Args:
            service_type: Type of service to get

        Returns:
            Service instance

        Raises:
            ServiceError: If service not found
        """
        service_name = service_type.__name__
        if service_name not in self._services:
            raise ServiceError(f"Service {service_name} not registered")

        return self._services[service_name]

    def initialize(self) -> None:
        """Initialize all registered services.

        Raises:
            ServiceError: If initialization fails
        """
        for service in self._services.values():
            try:
                if not service.initialized:
                    service.initialize()
            except Exception as e:
                raise ServiceError(f"Failed to initialize service: {str(e)}")

        self._initialized = True

    def cleanup(self) -> None:
        """Clean up all registered services."""
        for service in self._services.values():
            try:
                service.cleanup()
            except Exception:
                pass  # Ignore cleanup errors

        self._services.clear()
        self._initialized = False
