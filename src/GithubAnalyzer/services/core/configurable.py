"""Base class for configurable services."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from GithubAnalyzer.models.core.errors import ConfigError, ServiceError
from GithubAnalyzer.utils.logging import get_logger


class ConfigurableService(ABC):
    """Base class for services that require configuration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the configurable service.

        Args:
            config: Optional configuration dictionary.
        """
        self._config = self._validate_config(config or {})
        self._initialized = False

    @abstractmethod
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process configuration.

        Args:
            config: Configuration dictionary to validate.

        Returns:
            The validated configuration dictionary.

        Raises:
            ConfigError: If the configuration is invalid.
        """
        raise NotImplementedError

    @property
    def config(self) -> Dict[str, Any]:
        """Get the current configuration.

        Returns:
            The current configuration dictionary.
        """
        return self._config

    @property
    def initialized(self) -> bool:
        """Check if the service is initialized.

        Returns:
            True if initialized, False otherwise.
        """
        return self._initialized

    def update_config(self, config: Dict[str, Any]) -> None:
        """Update the service configuration.

        Args:
            config: New configuration dictionary.

        Raises:
            ConfigError: If the new configuration is invalid.
            ServiceError: If the service is initialized and cannot be reconfigured.
        """
        if self._initialized:
            raise ServiceError(
                "Cannot update configuration while service is initialized"
            )
        self._config = self._validate_config(config)
