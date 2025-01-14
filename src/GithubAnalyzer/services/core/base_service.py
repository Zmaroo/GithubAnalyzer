"""Base service definitions."""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from ...models.core.errors import ConfigError, ServiceError


class BaseService(ABC):
    """Base class for all services."""

    def __init__(self) -> None:
        """Initialize service."""
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Check if service is initialized.

        Returns:
            bool: True if service is initialized, False otherwise.
        """
        return self._initialized

    @abstractmethod
    def start(self) -> None:
        """Start the service.

        Raises:
            ServiceError: If service fails to start.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the service.

        Raises:
            ServiceError: If service fails to stop.
        """
        pass


class ConfigurableService(BaseService):
    """Base class for services with configuration."""

    def __init__(self, config: Optional[Dict] = None) -> None:
        """Initialize service with configuration.

        Args:
            config: Optional service configuration.
        """
        super().__init__()
        self._config = config or {}
        self.validate_config()

    def validate_config(self) -> None:
        """Validate service configuration.

        Raises:
            ConfigError: If configuration is invalid.
        """
        try:
            self._validate_config()
        except Exception as e:
            raise ConfigError(f"Invalid configuration: {e}") from e

    def get_config(self) -> Dict:
        """Get service configuration.

        Returns:
            Dict: Current configuration.
        """
        return self._config.copy()

    def start(self) -> None:
        """Start the service.

        Raises:
            ServiceError: If service fails to start.
        """
        if self._initialized:
            return

        try:
            self._start_impl()
            self._initialized = True
        except Exception as e:
            raise ServiceError(f"Failed to start service: {e}") from e

    def stop(self) -> None:
        """Stop the service.

        Raises:
            ServiceError: If service fails to stop.
        """
        if not self._initialized:
            return

        try:
            self._stop_impl()
            self._initialized = False
        except Exception as e:
            raise ServiceError(f"Failed to stop service: {e}") from e

    def _validate_config(self) -> None:
        """Validate service configuration.

        This method should be overridden by subclasses to implement
        specific configuration validation logic.

        Raises:
            ConfigError: If configuration is invalid.
        """
        pass

    def _start_impl(self) -> None:
        """Start service implementation.

        This method should be overridden by subclasses to implement
        specific start logic.

        Raises:
            ServiceError: If service fails to start.
        """
        pass

    def _stop_impl(self) -> None:
        """Stop service implementation.

        This method should be overridden by subclasses to implement
        specific stop logic.

        Raises:
            ServiceError: If service fails to stop.
        """
        pass
