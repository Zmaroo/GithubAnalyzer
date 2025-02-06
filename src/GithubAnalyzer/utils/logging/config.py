"""Logging configuration for GithubAnalyzer."""
import json
import logging
import logging.config
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from tree_sitter import LogType, Parser

from . import get_logger, get_tree_sitter_logger


class Environment(Enum):
    """Environment types for configuration."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

# Default log levels by environment
DEFAULT_LOG_LEVELS = {
    Environment.DEVELOPMENT: logging.DEBUG,
    Environment.TESTING: logging.DEBUG,
    Environment.PRODUCTION: logging.INFO
}

# Get environment from env var, default to development
ENVIRONMENT = Environment(os.getenv("GITHUB_ANALYZER_ENV", "development").lower())

# Base configuration
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "()": "GithubAnalyzer.utils.logging.StructuredFormatter",
            "indent": None if ENVIRONMENT == Environment.PRODUCTION else 2
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
            "level": DEFAULT_LOG_LEVELS[ENVIRONMENT]
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "structured",
            "filename": "logs/github_analyzer.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        }
    },
    "loggers": {
        "GithubAnalyzer": {
            "level": DEFAULT_LOG_LEVELS[ENVIRONMENT],
            "handlers": ["console", "file"],
            "propagate": False
        },
        "tree_sitter": {
            "level": DEFAULT_LOG_LEVELS[ENVIRONMENT],
            "handlers": ["console", "file"],
            "propagate": False
        }
    }
}

def configure_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """Configure logging with given config or defaults.
    
    Args:
        config: Optional custom logging configuration
    """
    # Use provided config or default
    log_config = config or LOG_CONFIG
    
    # Ensure log directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Apply configuration
    logging.config.dictConfig(log_config)
    
    # Log configuration applied
    logger = get_logger("GithubAnalyzer")
    logger.info(
        "Logging configured",
        extra={
            "context": {
                "environment": ENVIRONMENT.value,
                "log_level": logging.getLevelName(DEFAULT_LOG_LEVELS[ENVIRONMENT]),
                "config": log_config
            }
        }
    )

def configure_test_logging() -> Dict[str, Any]:
    """Configure logging for tests.
    
    Returns:
        Dictionary containing configured loggers and handlers
    """
    # Create main test logger
    main_logger = get_logger('test')
    
    # Create tree-sitter logger hierarchy
    ts_logger = get_tree_sitter_logger('tree_sitter')
    
    # Set debug level for all loggers
    main_logger.setLevel(logging.DEBUG)
    ts_logger.setLevel(logging.DEBUG)
    
    # Return dict of loggers for test verification
    return {
        'main_logger': main_logger,
        'ts_logger': ts_logger,
        'parser_logger': ts_logger.getChild('parser'),
        'query_logger': ts_logger.getChild('query')
    }

def configure_parser_logging(parser: Parser, logger_name: str = "tree_sitter") -> 'logging.Logger':
    """Configure logging for a tree-sitter parser.
    
    Args:
        parser: The parser to configure logging for
        logger_name: Base name for the logger
        
    Returns:
        The configured logger
    """
    # Get the tree-sitter logger
    ts_logger = get_tree_sitter_logger(logger_name)
    
    # Create a logging callback that handles both PARSE and LEX log types
    def logger_callback(log_type: LogType, msg: str) -> None:
        try:
            # Only log parse messages; ignore lex messages
            if log_type != LogType.PARSE:
                return
            context = {
                'source': 'tree-sitter',
                'type': 'parser',
                'log_type': 'parse'
            }
            ts_logger.debug(msg, extra={'context': context})
        except Exception as e:
            ts_logger.error("Exception in logger_callback: %s", str(e))
    
    # Set the logger on the parser
    parser.set_logger_callback(logger_callback)
    
    return ts_logger

# Tree-sitter logging configuration
TREE_SITTER_LOGGING_ENABLED = ENVIRONMENT in {Environment.DEVELOPMENT, Environment.TESTING} 