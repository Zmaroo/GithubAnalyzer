"""Logging configuration."""

import logging
import logging.config
from pathlib import Path
from typing import Optional

from ..models.core.config.settings import Settings


def configure_logging(settings: Optional[Settings] = None) -> None:
    """Configure logging for the application.
    
    Args:
        settings: Optional settings instance for custom configuration
    """
    log_level = getattr(settings, 'log_level', 'INFO') if settings else 'INFO'
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    
    # Basic configuration
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # Console handler
            logging.FileHandler(  # File handler
                filename=Path('logs/github_analyzer.log'),
                encoding='utf-8',
            )
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('tree_sitter').setLevel(logging.WARNING)
    logging.getLogger('GithubAnalyzer').setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
