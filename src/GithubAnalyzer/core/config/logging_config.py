"""
Module containing logging configuration for the GithubAnalyzer package.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any

def get_logging_config() -> Dict[str, Any]:
    """
    Get the logging configuration for the GithubAnalyzer package.
    
    Returns:
        Dict[str, Any]: The logging configuration dictionary.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    return {
        "version": 1,
        "level": logging.INFO,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default"
            }
        },
        "root": {
            "handlers": ["console"],
            "level": logging.INFO
        }
    } 