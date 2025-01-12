"""Performance optimization utilities"""
from typing import Any, Callable
from functools import lru_cache
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from ..config.settings import settings

logger = logging.getLogger(__name__)

def measure_time(func: Callable) -> Callable:
    """Measure execution time of function"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.debug(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

def batch_process(items: list, processor: Callable, batch_size: int = settings.BATCH_SIZE):
    """Process items in batches"""
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        yield processor(batch)

def parallel_process(items: list, processor: Callable, max_workers: int = 4):
    """Process items in parallel"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        yield from executor.map(processor, items)

@lru_cache(maxsize=1000)
def cached_operation(func: Callable) -> Callable:
    """Cache operation results"""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper 