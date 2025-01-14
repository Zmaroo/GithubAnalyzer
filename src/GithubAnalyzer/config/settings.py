"""Application settings and configuration.

This is the single source of truth for all application configuration.
All configuration values should be defined here and imported elsewhere.
"""

import os
from pathlib import Path
from typing import Any, Dict

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Environment settings
ENV = os.getenv("ENV", "development")
DEBUG_MODE = ENV == "development"
TESTING_MODE = ENV == "test"

# Parser settings
PARSER_TIMEOUT = int(os.getenv("PARSER_TIMEOUT", "5000"))  # 5 seconds
MAX_PARSE_SIZE = int(os.getenv("MAX_PARSE_SIZE", "5242880"))  # 5MB

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": LOG_LEVEL,
            "class": "logging.FileHandler",
            "filename": os.path.join(PROJECT_ROOT, "github_analyzer.log"),
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {"handlers": ["console", "file"], "level": LOG_LEVEL, "propagate": True}
    },
}
