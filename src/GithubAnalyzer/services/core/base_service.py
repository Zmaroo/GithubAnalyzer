"""Base service implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from GithubAnalyzer.models.core.errors import ServiceError
from GithubAnalyzer.utils.logging import get_logger


class BaseService(ABC):
    """Base class for all services."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the service.

        Args:
            config: Optional service configuration dictionary.

        Raises:
            ServiceError: If configuration is invalid.
        """
        self._initialized = False
        self._config = self._validate_config(config or {})
        # Use application-level logging
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")

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
