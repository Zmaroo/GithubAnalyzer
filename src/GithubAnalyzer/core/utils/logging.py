"""Logging configuration."""

import logging
import logging.config
from typing import Optional, Dict, Any
from functools import wraps

from ..config.logging_config import get_logging_config

def configure_logging(config: Optional[Dict[str, Any]] = None, env: Optional[str] = None) -> None:
    """Configure logging with optional custom config.
    
    Args:
        config: Optional custom logging configuration
        env: Optional environment name for default config
    """
    if config is None:
        config = get_logging_config(env)
    
    logging.config.dictConfig(config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name, typically __name__
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def log_exceptions(logger: Optional[logging.Logger] = None):
    """Decorator to log exceptions.
    
    Args:
        logger: Optional logger instance. If None, uses root logger.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = logging.getLogger()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Exception in {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator

class StructuredLogger:
    """Logger that adds structured context to log messages."""
    
    def __init__(self, name: str):
        """Initialize structured logger.
        
        Args:
            name: Logger name
        """
        self._logger = logging.getLogger(name)
        self._context = {}
    
    def add_context(self, **kwargs) -> None:
        """Add context data to be included in all log messages."""
        self._context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear all context data."""
        self._context.clear()
    
    def _format_message(self, msg: str) -> str:
        """Format message with context data."""
        if self._context:
            context_str = " ".join(f"{k}={v}" for k, v in self._context.items())
            return f"{msg} [{context_str}]"
        return msg
    
    def debug(self, msg: str, **kwargs) -> None:
        """Log debug message with context."""
        context = {**self._context, **kwargs}
        self._logger.debug(self._format_message(msg), extra=context)
    
    def info(self, msg: str, **kwargs) -> None:
        """Log info message with context."""
        context = {**self._context, **kwargs}
        self._logger.info(self._format_message(msg), extra=context)
    
    def warning(self, msg: str, **kwargs) -> None:
        """Log warning message with context."""
        context = {**self._context, **kwargs}
        self._logger.warning(self._format_message(msg), extra=context)
    
    def error(self, msg: str, **kwargs) -> None:
        """Log error message with context."""
        context = {**self._context, **kwargs}
        self._logger.error(self._format_message(msg), extra=context)
    
    def exception(self, msg: str, **kwargs) -> None:
        """Log exception message with context."""
        context = {**self._context, **kwargs}
        self._logger.exception(self._format_message(msg), extra=context)
