"""Service registry implementation."""

from typing import Any, Dict, Optional, Type

from ...models.core.errors import ServiceError
from .base_service import BaseService


class BusinessTools:
    """Registry for business tools and services."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._services: Dict[str, BaseService] = {}
        self._service_types: Dict[str, Type[BaseService]] = {}

    def register_service_type(self, name: str, service_type: Type[BaseService]) -> None:
        """Register a service type.

        Args:
            name: The name of the service.
            service_type: The service class to register.

        Raises:
            ServiceError: If the service type is already registered.
        """
        if name in self._service_types:
            raise ServiceError(f"Service type {name} is already registered")
        self._service_types[name] = service_type

    def create_service(
        self, name: str, config: Optional[Dict[str, Any]] = None
    ) -> BaseService:
        """Create and register a service instance.

        Args:
            name: The name of the service.
            config: Optional configuration for the service.

        Returns:
            The created service instance.

        Raises:
            ServiceError: If the service type is not registered.
        """
        if name not in self._service_types:
            raise ServiceError(f"Service type {name} is not registered")

        service_type = self._service_types[name]
        service = service_type(config or {})
        self._services[name] = service
        return service

    def get_service(self, name: str) -> Optional[BaseService]:
        """Get a registered service instance.

        Args:
            name: The name of the service.

        Returns:
            The service instance if found, None otherwise.
        """
        return self._services.get(name)

    def has_service(self, name: str) -> bool:
        """Check if a service is registered.

        Args:
            name: The name of the service.

        Returns:
            True if the service is registered, False otherwise.
        """
        return name in self._services

    def initialize_services(self) -> None:
        """Initialize all registered services.

        Raises:
            ServiceError: If any service fails to initialize.
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
