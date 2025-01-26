"""Timing utilities for performance monitoring."""
import time
import functools
from typing import Callable, TypeVar, ParamSpec
from GithubAnalyzer.utils.logging.logging_config import get_logger

logger = get_logger(__name__)

P = ParamSpec('P')
T = TypeVar('T')

def timer(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator to time function execution."""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        logger.debug({
            "message": f"{func.__name__} execution time",
            "context": {
                "function": func.__name__,
                "duration_ms": duration * 1000,
                "args_count": len(args),
                "kwargs_count": len(kwargs)
            }
        })
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
        logger.debug({
            "message": f"{self.name} execution time",
            "context": {
                "block_name": self.name,
                "duration_ms": duration * 1000,
                "error": str(exc_val) if exc_val else None
            }
        })

__all__ = ['Timer', 'timer'] 