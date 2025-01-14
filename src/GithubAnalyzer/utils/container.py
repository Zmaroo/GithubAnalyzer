"""Service container implementation."""

from typing import Any, Dict, Optional, Type, TypeVar, cast

from GithubAnalyzer.models.core.errors import ServiceError, ServiceNotFoundError
from GithubAnalyzer.services.core.base_service import BaseService

S = TypeVar("S", bound=BaseService)


class ServiceContainer:
    """Container for managing services."""

    def __init__(self) -> None:
        """Initialize the service container."""
        self._services: Dict[str, BaseService] = {}

    def register_service(self, name: str, service: BaseService) -> None:
        """Register a service.

        Args:
            name: Name of the service
            service: Service instance to register

        Raises:
            ServiceError: If service is already registered
        """
        if name in self._services:
            raise ServiceError(f"Service {name} already registered")
        self._services[name] = service

    def get_service(self, name: str, service_type: Type[S]) -> S:
        """Get a registered service.

        Args:
            name: Name of the service
            service_type: Type of service to return

        Returns:
            Service instance

        Raises:
            ServiceNotFoundError: If service is not found
            ServiceError: If service is of wrong type
        """
        service = self._services.get(name)
        if not service:
            raise ServiceNotFoundError(f"Service {name} not found")

        if not isinstance(service, service_type):
            raise ServiceError(f"Service {name} is not of type {service_type.__name__}")

        return cast(S, service)

    def has_service(self, name: str) -> bool:
        """Check if a service is registered.

        Args:
            name: Name of the service

        Returns:
            True if service is registered, False otherwise
        """
        return name in self._services

    def initialize_services(self) -> None:
        """Initialize all registered services.

        Raises:
            ServiceError: If initialization fails
        """
        for name, service in self._services.items():
            try:
                service.initialize()
            except Exception as e:
                raise ServiceError(f"Failed to initialize service {name}: {str(e)}")

    def cleanup_services(self) -> None:
        """Clean up all registered services."""
        for service in self._services.values():
            try:
                service.cleanup()
            except Exception:
                pass  # Ignore cleanup errors
        self._services.clear()
