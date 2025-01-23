"""Error handling utilities."""

import logging
import traceback
from typing import Any, Dict, Optional, Type, TypeVar, Callable
from functools import wraps

from ..models.errors import ParserError, FileOperationError

T = TypeVar('T')
logger = logging.getLogger(__name__)

def handle_errors(
    error_type: Type[Exception] = Exception,
    message: Optional[str] = None,
    reraise: bool = True,
    log_level: int = logging.ERROR
) -> Callable:
    """Decorator for handling errors.
    
    Args:
        error_type: Type of error to catch
        message: Error message prefix
        reraise: Whether to reraise the error
        log_level: Logging level for error
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except error_type as e:
                error_msg = f"{message}: {str(e)}" if message else str(e)
                logger.log(log_level, error_msg, exc_info=True)
                if reraise:
                    raise
            return None  # type: ignore
        return wrapper
    return decorator

__all__ = ['handle_errors'] 