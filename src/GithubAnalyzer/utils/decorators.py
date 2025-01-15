"""Utility decorators"""

import functools
import time
from typing import Any, Callable, Optional, Type, TypeVar

T = TypeVar('T')

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """Retry a function on failure.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception  # type: ignore
        return wrapper
    return decorator


def timeout(seconds: float) -> Callable:
    """Timeout decorator.

    Args:
        seconds: Timeout in seconds

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            import signal

            def handler(signum: int, frame: Optional[Any]) -> None:
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")

            # Set the timeout handler
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(int(seconds))

            try:
                result = func(*args, **kwargs)
            finally:
                # Disable the alarm
                signal.alarm(0)
            return result
        return wrapper
    return decorator
