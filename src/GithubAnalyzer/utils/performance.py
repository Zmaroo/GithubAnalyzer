"""Performance monitoring and measurement utilities."""

import functools
import time
from typing import Any, Callable, Dict

import psutil


def measure_time(func: Callable) -> Callable:
    """Measure execution time of a function.

    Args:
        func: Function to measure.

    Returns:
        Wrapped function.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result

    return wrapper


def monitor_memory(threshold_mb: float = 100.0) -> Callable:
    """Monitor memory usage of a function.

    Args:
        threshold_mb: Memory threshold in MB.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            process = psutil.Process()
            start_mem = process.memory_info().rss / 1024 / 1024
            result = func(*args, **kwargs)
            end_mem = process.memory_info().rss / 1024 / 1024
            used_mem = end_mem - start_mem
            if used_mem > threshold_mb:
                print(f"Warning: {func.__name__} used {used_mem:.1f}MB of memory")
            return result

        return wrapper

    return decorator


def check_memory_usage() -> Dict[str, float]:
    """Check current memory usage.

    Returns:
        Dict containing memory usage metrics in MB.
    """
    process = psutil.Process()
    memory_info = process.memory_info()

    return {
        "rss": memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
        "vms": memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
        "shared": getattr(memory_info, "shared", 0)
        / 1024
        / 1024,  # Shared memory in MB
        "data": getattr(memory_info, "data", 0)
        / 1024
        / 1024,  # Data segment memory in MB
    }
