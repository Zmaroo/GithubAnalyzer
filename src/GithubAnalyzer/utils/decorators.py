"""Utility decorators"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Retry decorator with exponential backoff"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            current_delay = delay

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {e}")
                        raise

                    logger.warning(
                        f"Attempt {attempt} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            return None  # Should never reach here

        return wrapper

    return decorator


def singleton(cls: Type[T]) -> Type[T]:
    """
    Decorator to make a class a singleton.

    Args:
        cls: The class to make singleton

    Returns:
        The singleton class
    """
    instances = {}

    @wraps(cls)
    def get_instance(*args: Any, **kwargs: Any) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def cache_result(func: Callable) -> Callable:
    """
    Cache function results.

    Args:
        func: Function to cache results for

    Returns:
        Wrapped function with caching
    """
    cache = {}

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        key = str(args) + str(sorted(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return wrapper
