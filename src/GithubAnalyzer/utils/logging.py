"""Logging configuration."""

import logging
import logging.config
from typing import Optional

from ..config.settings import Settings, LOGGING

def configure_logging(config: Optional[dict] = None) -> None:
    """Configure logging with optional custom config."""
    if config is None:
        config = LOGGING
    
    logging.config.dictConfig(config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
