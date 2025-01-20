"""Utility decorators for error handling and performance."""

import functools
import logging
import signal
import time
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar, Union
from types import TracebackType

from ..models.errors import ParserError, TimeoutError

T = TypeVar('T')
logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (ParserError,)
) -> Callable:
    """Retry a function on failure with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay between retries
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function
        
    Example:
        @retry(max_attempts=3, delay=1.0)
        def parse_file(path: str) -> Dict:
            # Function implementation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed. "
                            f"Last error: {str(e)}"
                        )
            
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected error in retry logic")
            
        return wrapper
    return decorator


def timeout(seconds: float) -> Callable:
    """Timeout decorator for long-running operations.
    
    Args:
        seconds: Timeout duration in seconds
        
    Returns:
        Decorated function
        
    Raises:
        TimeoutError: If function execution exceeds timeout
        
    Example:
        @timeout(5.0)
        def parse_large_file(path: str) -> Dict:
            # Function implementation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            def handler(signum: int, frame: Optional[Any]) -> None:
                raise TimeoutError(
                    f"Function {func.__name__} timed out after {seconds} seconds"
                )

            # Set up the timeout handler
            original_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(int(seconds))

            try:
                result = func(*args, **kwargs)
            finally:
                # Restore original handler and clear alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, original_handler)
                
            return result
        return wrapper
    return decorator


class timer:
    """Context manager and decorator for timing operations.
    
    Example as decorator:
        @timer()
        def parse_file(path: str) -> Dict:
            # Function implementation
            
    Example as context manager:
        with timer() as t:
            result = parse_file(path)
            print(f"Parsing took {t.elapsed:.2f}s")
    """
    
    def __init__(self, name: Optional[str] = None):
        """Initialize timer.
        
        Args:
            name: Optional name for the timed operation
        """
        self.name = name
        self.start_time: float = 0
        self.end_time: float = 0
        
    def __enter__(self) -> 'timer':
        """Start timing."""
        self.start_time = time.time()
        return self
        
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        """Stop timing."""
        self.end_time = time.time()
        if self.name:
            logger.info(f"{self.name} took {self.elapsed:.2f}s")
            
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Use as decorator."""
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with self:
                return func(*args, **kwargs)
        return wrapper
        
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
