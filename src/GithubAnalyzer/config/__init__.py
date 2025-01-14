"""Configuration package.

This package provides access to all application configuration.
Import settings from here rather than directly from settings.py.
"""

from .settings import (
    BASE_DIR,
    DEBUG_MODE,
    ENV,
    LOG_LEVEL,
    LOGGING,
    MAX_PARSE_SIZE,
    PARSER_TIMEOUT,
    PROJECT_ROOT,
    TESTING_MODE,
)

__all__ = [
    "BASE_DIR",
    "DEBUG_MODE",
    "ENV",
    "LOG_LEVEL",
    "LOGGING",
    "MAX_PARSE_SIZE",
    "PARSER_TIMEOUT",
    "PROJECT_ROOT",
    "TESTING_MODE",
]
