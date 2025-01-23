"""Timing utilities."""
import time
from typing import Optional, Type, TypeVar, Callable, Any
from types import TracebackType
import logging
from functools import wraps
from src.GithubAnalyzer.core.utils.logging import get_logger

T = TypeVar('T')
logger = logging.getLogger(__name__)

class Timer:
    """Context manager and decorator for timing operations."""
    
    logger = get_logger(__name__)
    
    def __init__(self, name: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.name = name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time: float = 0
        self.end_time: float = 0
        
    def __enter__(self) -> 'Timer':
        self.start_time = time.time()
        return self
        
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        self.end_time = time.time()
        if self.name:
            self.logger.info(f"{self.name} took {self.elapsed:.2f}s")
            
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with self:
                return func(*args, **kwargs)
        return wrapper
        
    @property
    def elapsed(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time 

def timer(func: Callable[..., T]) -> Callable[..., T]:
    """Timer decorator."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        with Timer(func.__name__):
            return func(*args, **kwargs)
    return wrapper

__all__ = ['Timer', 'timer'] 