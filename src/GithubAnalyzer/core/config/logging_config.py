"""
Module containing logging configuration for the GithubAnalyzer package.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

def get_logging_config(env: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the logging configuration for the GithubAnalyzer package.
    
    Args:
        env: Optional environment name
        
    Returns:
        Dict[str, Any]: The logging configuration dictionary.
    """
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(levelname)s - %(message)s"
            },
            "structured": {
                "()": "src.GithubAnalyzer.core.utils.logging.StructuredFormatter",
                "format": json.dumps({
                    "timestamp": "%(asctime)s",
                    "level": "%(levelname)s",
                    "logger": "%(name)s",
                    "thread": "%(thread)d",
                    "message": "%(message)s",
                    "context": "%(context)s"
                })
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard"
            },
            "file": {
                "class": "logging.handlers.QueueHandler",
                "level": "DEBUG",
                "formatter": "structured",
                "queue": "src.GithubAnalyzer.core.utils.logging.get_log_queue()"
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": "INFO",
                "propagate": True
            },
            "src.GithubAnalyzer": {
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": True
            },
            "tree_sitter": {  # Logger for tree-sitter operations
                "handlers": ["file"],
                "level": "DEBUG",
                "propagate": True
            }
        }
    }