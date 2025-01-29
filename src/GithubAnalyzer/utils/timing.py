"""Timing utilities for performance monitoring."""
import time
import functools
import sys
from typing import Callable, TypeVar, ParamSpec

from .logging import get_logger

P = ParamSpec('P')
T = TypeVar('T')

logger = get_logger(__name__)

def timer(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator to time function execution."""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        logger.debug(f"{func.__name__} execution time: {duration * 1000:.2f}ms")
        return result
    return wrapper

class Timer:
    """Context manager for timing code blocks."""
    
    def __init__(self, name: str):
        """Initialize timer with a name."""
        self.name = name
        self.start_time = 0.0
        
    def __enter__(self) -> 'Timer':
        """Start timing."""
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop timing and log duration."""
        duration = time.time() - self.start_time
        logger.debug(f"{self.name} execution time: {duration * 1000:.2f}ms")

__all__ = ['Timer', 'timer'] 