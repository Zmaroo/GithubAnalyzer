"""Logging configuration."""

import logging
import logging.config
from pathlib import Path
from typing import Optional

from ..models.core.config.settings import Settings

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent.parent.parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Default log file path
DEFAULT_LOG_FILE = LOGS_DIR / 'github_analyzer.log'


def configure_logging(settings: Optional[Settings] = None) -> None:
    """Configure logging for the application.
    
    Args:
        settings: Optional settings instance for custom configuration
    """
    log_level = getattr(settings, 'log_level', 'INFO') if settings else 'INFO'
    
    # Ensure logs directory exists
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Configure logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'file': {
                'level': log_level,
                'formatter': 'detailed',
                'class': 'logging.FileHandler',
                'filename': str(DEFAULT_LOG_FILE),
                'mode': 'a',
                'encoding': 'utf-8',
            },
            'error_file': {
                'level': 'ERROR',
                'formatter': 'detailed',
                'class': 'logging.FileHandler',
                'filename': str(LOGS_DIR / 'error.log'),
                'mode': 'a',
                'encoding': 'utf-8',
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': True
            },
            'GithubAnalyzer': {  # Application logger
                'handlers': ['console', 'file', 'error_file'],
                'level': log_level,
                'propagate': False
            },
            'tree_sitter': {  # Tree-sitter logger
                'handlers': ['file'],
                'level': 'WARNING',
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
