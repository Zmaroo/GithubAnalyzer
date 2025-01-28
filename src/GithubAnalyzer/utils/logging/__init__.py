"""Logging utilities for GithubAnalyzer."""

import logging
import sys
import json
from typing import Optional, Dict, Any
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def configure_logging(
    level: int = logging.INFO,
    structured: bool = True,
    enable_tree_sitter: bool = False,
    log_file: Optional[str] = None,
    indent: Optional[int] = 2
) -> None:
    """Configure logging for the application."""
    from .logging_config import configure_logging as _configure
    _configure(level, structured, enable_tree_sitter, log_file, indent)

__all__ = [
    'configure_logging',
    'get_logger'
] 