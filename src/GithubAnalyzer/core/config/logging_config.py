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
            "detailed": {
                "format": "%(levelname)-8s %(name)s:%(filename)s:%(lineno)d %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "standard"
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/github_analyzer.log",
                "mode": "a"
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": True
            },
            "src.GithubAnalyzer": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False
            },
            "tree_sitter": {  # Logger for tree-sitter operations
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False
            },
            "test_structured": {  # Logger for structured logging tests
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False
            }
        }
    } 