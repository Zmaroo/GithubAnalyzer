"""Base service implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from GithubAnalyzer.models.core.errors import ServiceError


class BaseService(ABC):
    """Base class for all services."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the service.

        Args:
            config: Service configuration dictionary.

        Raises:
            ServiceError: If configuration is invalid.
        """
        self._initialized = False
        self._config = self._validate_config(config)

    @abstractmethod
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the service configuration.

        Args:
            config: Configuration dictionary to validate.

        Returns:
            The validated configuration dictionary.

        Raises:
            ServiceError: If configuration is invalid.
        """
        if not isinstance(config, dict):
            raise ServiceError("Configuration must be a dictionary")
        return config

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service.

        Raises:
            ServiceError: If initialization fails.
        """
        pass

    @property
    def initialized(self) -> bool:
        """Check if service is initialized.

        Returns:
            True if service is initialized, False otherwise.
        """
        return self._initialized

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up service resources."""
        pass
