"""Tests for the cache service.

This module contains tests for verifying proper functionality
of the cache service component.
"""

import pytest
from threading import Thread
from typing import Optional

from GithubAnalyzer.core.models.errors import ServiceError
from GithubAnalyzer.common.services.cache_service import CacheService

@pytest.fixture
def cache_service() -> CacheService:
    """Create a CacheService instance."""
    return CacheService(max_size=100)

def test_basic_cache_operations(cache_service: CacheService) -> None:
    """Test basic cache operations."""
    # Set and get
    cache_service.set("test_cache", "key1", "value1")
    assert cache_service.get("test_cache", "key1") == "value1"
    
    # Delete
    cache_service.delete("test_cache", "key1")
    assert cache_service.get("test_cache", "key1") is None
    
    # Clear
    cache_service.set("test_cache", "key2", "value2")
    cache_service.clear("test_cache")
    assert cache_service.get("test_cache", "key2") is None

def test_cache_size_limit(cache_service: CacheService) -> None:
    """Test cache size limit."""
    # Fill cache to limit
    for i in range(100):
        cache_service.set("test_cache", f"key{i}", f"value{i}")
        
    # Try to add one more item
    with pytest.raises(ServiceError, match="Cache test_cache is full"):
        cache_service.set("test_cache", "overflow", "value")

def test_multiple_caches(cache_service: CacheService) -> None:
    """Test multiple cache instances."""
    cache_service.set("cache1", "key", "value1")
    cache_service.set("cache2", "key", "value2")
    
    assert cache_service.get("cache1", "key") == "value1"
    assert cache_service.get("cache2", "key") == "value2"
    
    cache_service.clear("cache1")
    assert cache_service.get("cache1", "key") is None
    assert cache_service.get("cache2", "key") == "value2"

def test_thread_safety(cache_service: CacheService) -> None:
    """Test thread safety of cache operations."""
    def worker(cache_name: str, start: int, results: list) -> None:
        try:
            for i in range(start, start + 10):
                cache_service.set(cache_name, f"key{i}", i)
                value = cache_service.get(cache_name, f"key{i}")
                results.append(value == i)
        except ServiceError:
            # Cache might be full, which is expected
            pass
    
    results: list[bool] = []
    threads = [
        Thread(target=worker, args=(f"cache{i}", i*10, results))
        for i in range(5)
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    assert all(results), "Some cache operations failed in threads"

def test_cleanup(cache_service: CacheService) -> None:
    """Test cache cleanup."""
    cache_service.set("cache1", "key", "value")
    cache_service.set("cache2", "key", "value")
    
    cache_service.cleanup()
    
    assert cache_service.get("cache1", "key") is None
    assert cache_service.get("cache2", "key") is None 