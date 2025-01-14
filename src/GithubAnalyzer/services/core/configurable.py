"""Configurable service base class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from GithubAnalyzer.models.core.errors import ServiceError


class ConfigurableService(ABC):
    """Base class for configurable services."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._config: Dict[str, Any] = {}
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the service.

        Args:
            config: Configuration dictionary

        Raises:
            ServiceError: If configuration is invalid
        """
        try:
            self.validate_config(config)
            self._config.update(config)
        except Exception as e:
            raise ServiceError(f"Invalid configuration: {str(e)}")

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration.

        Args:
            config: Configuration to validate

        Raises:
            ServiceError: If configuration is invalid
        """

    @abstractmethod
    def start(self) -> None:
        """Start the service.

        Raises:
            ServiceError: If service fails to start
        """

    @abstractmethod
    def stop(self) -> None:
        """Stop the service.

        Raises:
            ServiceError: If service fails to stop
        """

    def get_config(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self._config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value

        Raises:
            ServiceError: If configuration is invalid
        """
        config = self._config.copy()
        config[key] = value
        self.validate_config(config)
        self._config[key] = value
