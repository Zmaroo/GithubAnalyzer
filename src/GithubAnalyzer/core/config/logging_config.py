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
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_dir / "github_analyzer.log"),
                "mode": "a"
            }
        },
        "loggers": {
            "GithubAnalyzer": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"]
        }
    } 