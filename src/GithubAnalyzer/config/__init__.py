"""Configuration package."""

from pathlib import Path
from typing import Dict, Any

# Import settings
from .settings import (
    Settings,
    settings,
    BASE_DIR,
    PROJECT_ROOT,
    MAX_FILE_SIZE,
    DEBUG_MODE,
    TESTING_MODE,
    ENV,
    LOG_LEVEL,
    PARSER_TIMEOUT,
    LOGGING,
)

# Import language config
from .language_config import (
    TREE_SITTER_LANGUAGES,
    PARSER_LANGUAGE_MAP,
    get_language_variant,
)

__all__ = [
    "Settings",
    "settings",
    "BASE_DIR",
    "PROJECT_ROOT",
    "MAX_FILE_SIZE",
    "DEBUG_MODE",
    "TESTING_MODE",
    "ENV",
    "LOG_LEVEL",
    "PARSER_TIMEOUT",
    "LOGGING",
    "TREE_SITTER_LANGUAGES",
    "PARSER_LANGUAGE_MAP",
    "get_language_variant",
]
