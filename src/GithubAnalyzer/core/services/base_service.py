"""Base service class with configuration management."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging

from ..models.errors import ConfigError, ServiceError

logger = logging.getLogger(__name__)

class BaseService(ABC):
    """Base class for all services with configuration management."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the service.

        Args:
            config: Optional service configuration dictionary.

        Raises:
            ConfigError: If configuration is invalid.
        """
        self._initialized = False
        self._config = self._validate_config(config or {})
        self.logger = logger.getChild(self.__class__.__name__)

    @abstractmethod
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process configuration.

        Args:
            config: Configuration dictionary to validate.

        Returns:
            The validated configuration dictionary.

        Raises:
            ConfigError: If configuration is invalid.
        """
        if not isinstance(config, dict):
            raise ConfigError("Configuration must be a dictionary")
        return config

    @property
    def config(self) -> Dict[str, Any]:
        """Get the current configuration.

        Returns:
            The current configuration dictionary.
        """
        return self._config

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

    @abstractmethod
    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize the service.

        Args:
            languages: Optional list of languages to initialize support for.

        Raises:
            ServiceError: If initialization fails.
        """

    @property
    def initialized(self) -> bool:
        """Check if service is initialized.

        Returns:
            True if service is initialized, False otherwise.
        """
        return self._initialized

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up service resources.
        
        This method should:
        1. Release any system resources
        2. Clear caches and temporary data
        3. Reset internal state
        """
