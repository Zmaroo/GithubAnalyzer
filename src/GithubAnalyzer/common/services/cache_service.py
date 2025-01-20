"""Cache service for storing and retrieving data."""

from collections import defaultdict
from threading import Lock
from typing import Any, Dict, List, Optional

from ...core.models.errors import ServiceError, ConfigError
from ...core.services.base_service import BaseService

class CacheService(BaseService):
    """Service for caching data in memory."""

    def __init__(self, max_size: Optional[int] = None):
        """Initialize cache service.
        
        Args:
            max_size: Optional maximum number of items to cache
        """
        super().__init__()
        self._max_size = max_size
        self._caches: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._lock = Lock()

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            The validated configuration dictionary
            
        Raises:
            ConfigError: If configuration is invalid
        """
        # No config needed for cache service
        return config

    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize the cache service.
        
        Args:
            languages: Not used by cache service
        """
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