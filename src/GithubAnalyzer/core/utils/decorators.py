"""Utility decorators for error handling and performance."""

import functools
import logging
import signal
import time
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar, Union
from types import TracebackType

from ..models.errors import ParserError, TimeoutError, BaseError, ServiceError
from .error_handler import ErrorHandler

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

def wrap_errors(
    error_type: Type[BaseError] = ServiceError,
    context: str = "",
    recovery_fn: Optional[Callable] = None,
    retry_count: int = 0,
    retry_delay: float = 1.0,
    timeout: Optional[float] = None
) -> Callable:
    """Decorator to wrap function errors with retry and timeout.
    
    Args:
        error_type: Type of error to raise
        context: Error context message
        recovery_fn: Optional recovery function to call
        retry_count: Number of retries
        retry_delay: Delay between retries
        timeout: Optional timeout in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error = None
            current_delay = retry_delay

            for attempt in range(max(1, retry_count + 1)):
                try:
                    if timeout:
                        return _with_timeout(timeout, func, *args, **kwargs)
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if recovery_fn:
                        recovery_fn()
                    if attempt < retry_count:
                        logger.warning(
                            f"Attempt {attempt + 1}/{retry_count + 1} failed: {str(e)}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= 2
                    else:
                        ErrorHandler.handle_error(
                            e,
                            context or f"Error in {func.__name__}",
                            error_type
                        )
            
            if last_error:
                raise last_error
            raise RuntimeError("Unexpected error in retry logic")
        return wrapper
    return decorator

def _with_timeout(seconds: float, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Execute function with timeout."""
    def handler(signum: int, frame: Optional[Any]) -> None:
        raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")

    original_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(int(seconds))

    try:
        return func(*args, **kwargs)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)
