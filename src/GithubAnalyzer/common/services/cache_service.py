"""Cache service for storing and retrieving data."""

from collections import defaultdict
from threading import Lock
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

from ...core.models.errors import ServiceError, ConfigError
from ...core.services.base_service import BaseService

class CacheService(BaseService):
    """Service for caching parsed data."""

    logger = logging.getLogger(__qualname__)  # Class-level logger

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize cache service."""
        default_config = {
            "max_size": 1000,  # Default max cache size
            "cache_dir": str(Path.home() / ".cache" / "github_analyzer")
        }
        if config:
            default_config.update(config)
        super().__init__(default_config)
        self.logger.info("Initializing cache service")
        self._max_size = default_config["max_size"]
        self._caches: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._lock = Lock()

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process configuration."""
        config = super()._validate_config(config)
        
        # Validate max_size if provided
        if "max_size" in config:
            if not isinstance(config["max_size"], int):
                raise ConfigError("max_size must be an integer")
            if config["max_size"] <= 0:
                raise ConfigError("max_size must be positive")
            
        # Validate cache_dir
        if "cache_dir" in config:
            if not isinstance(config["cache_dir"], str):
                raise ConfigError("cache_dir must be a string")
            
        return config

    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize the cache service."""
        self._caches = defaultdict(dict)
        self._lock = Lock()
        self._initialized = True

    def get(self, cache_name: str, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            cache_name: Name of cache to get from
            key: Key to get
            
        Returns:
            Cached value or None if not found
        """
        with self._lock:
            return self._caches[cache_name].get(key)

    def set(self, cache_name: str, key: str, value: Any) -> None:
        """Set value in cache.
        
        Args:
            cache_name: Name of cache to set in
            key: Key to set
            value: Value to cache
            
        Raises:
            ServiceError: If cache is full
        """
        with self._lock:
            if (self._max_size and 
                len(self._caches[cache_name]) >= self._max_size):
                raise ServiceError(f"Cache {cache_name} is full")
            self._caches[cache_name][key] = value

    def delete(self, cache_name: str, key: str) -> None:
        """Delete value from cache.
        
        Args:
            cache_name: Name of cache to delete from
            key: Key to delete
        """
        with self._lock:
            if key in self._caches[cache_name]:
                del self._caches[cache_name][key]

    def clear(self, cache_name: str) -> None:
        """Clear all values from a cache.
        
        Args:
            cache_name: Name of cache to clear
        """
        with self._lock:
            self._caches[cache_name].clear()

    def cleanup(self) -> None:
        """Clean up all caches."""
        with self._lock:
            self._caches.clear()

    def get_required_config_fields(self) -> List[str]:
        """Get required configuration fields."""
        return ["cache_dir", "max_size"] 