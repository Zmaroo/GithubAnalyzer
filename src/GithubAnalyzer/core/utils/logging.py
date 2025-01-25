"""Logging utilities."""

import logging
import logging.config
from typing import Optional, Dict, Any
from functools import wraps

def get_logging_config(env: Optional[str] = None) -> Dict[str, Any]:
    """Get logging configuration.
    
    Args:
        env: Optional environment name
        
    Returns:
        Logging configuration dictionary
    """
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(levelname)s - %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'default': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'level': 'DEBUG',
                'formatter': 'detailed',
                'class': 'logging.FileHandler',
                'filename': 'github_analyzer.log'
            }
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }
    
    # Environment-specific settings
    if env == 'test':
        config['loggers']['']['level'] = 'DEBUG'
        config['loggers']['']['handlers'] = ['default', 'file']
        
    return config

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
        """Add context key-value pairs."""
        self._context.update(kwargs)
        
    def clear_context(self) -> None:
        """Clear all context data."""
        self._context.clear()
        
    def _format_context(self, extra: Optional[Dict[str, Any]] = None) -> str:
        """Format context and extra data into string."""
        context = self._context.copy()
        if extra:
            context.update(extra)
        if not context:
            return ""
        return " [" + " ".join(f"{k}={v}" for k, v in context.items()) + "]"
        
    def _format_message(self, msg: str, **kwargs) -> str:
        """Format a message with context.
        
        Args:
            msg: The message to format
            **kwargs: Additional context key-value pairs
            
        Returns:
            The formatted message with context
        """
        # Combine context and kwargs
        context = self._context.copy()
        if kwargs:
            context.update(kwargs)
        
        # Format context if present
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in sorted(context.items()))
            return f"{msg} [{context_str}]"
        
        return msg
        
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message.
        
        Args:
            message: Message to log
            **kwargs: Additional context
        """
        self._logger.debug(self._format_message(message, **kwargs))
        
    def info(self, message: str, **kwargs) -> None:
        """Log info message.
        
        Args:
            message: Message to log
            **kwargs: Additional context
        """
        self._logger.info(self._format_message(message, **kwargs))
        
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message.
        
        Args:
            message: Message to log
            **kwargs: Additional context
        """
        self._logger.warning(self._format_message(message, **kwargs))
        
    def error(self, message: str, **kwargs) -> None:
        """Log error message.
        
        Args:
            message: Message to log
            **kwargs: Additional context
        """
        self._logger.error(self._format_message(message, **kwargs))
        
    def exception(self, message: str, **kwargs) -> None:
        """Log exception message.
        
        Args:
            message: Message to log
            **kwargs: Additional context
        """
        self._logger.exception(self._format_message(message, **kwargs))
