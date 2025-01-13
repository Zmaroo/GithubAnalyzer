"""Performance monitoring utilities"""
import time
import logging
from functools import wraps
from typing import Callable, Any
from ..config.settings import settings

logger = logging.getLogger(__name__)

def measure_time(func: Callable) -> Callable:
    """Measure execution time of a function"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        
        logger.debug(f"{func.__name__} took {duration:.2f} seconds")
        return result
    return wrapper

def check_memory_usage(size: int) -> bool:
    """Check if operation would exceed memory limit"""
    # Simple memory check - could be more sophisticated
    return size <= settings.memory_limit 