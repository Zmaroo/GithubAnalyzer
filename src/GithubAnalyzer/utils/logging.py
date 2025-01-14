"""Logging utilities."""

import logging
import logging.config
from typing import Optional

from GithubAnalyzer.config import settings


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """Set up and configure a logger.

    Args:
        name: Logger name. If None, returns root logger.

    Returns:
        Configured logger instance
    """
    # Configure logging if not already configured
    if not logging.getLogger().handlers:
        logging.config.dictConfig(settings.LOGGING)

    # Get and return logger
    logger = logging.getLogger(name) if name else logging.getLogger()
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.

    This is an alias for setup_logger for consistency with standard logging.

    Args:
        name: Logger name. If None, returns root logger.

    Returns:
        Logger instance
    """
    return setup_logger(name)
