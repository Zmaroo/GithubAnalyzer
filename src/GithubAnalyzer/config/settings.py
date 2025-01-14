"""Application settings and configuration.

This is the single source of truth for all application configuration.
All configuration values should be defined here and imported elsewhere.
"""

import os
from pathlib import Path
from typing import Any, Dict, List

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Environment settings
ENV = os.getenv("ENV", "development")
DEBUG_MODE = ENV == "development"
TESTING_MODE = ENV == "test"

# Redis configuration
REDIS_CONFIG: Dict[str, Any] = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", "6379")),
    "db": int(os.getenv("REDIS_DB", "0")),
    "password": os.getenv("REDIS_PASSWORD", None),
    "ssl": bool(os.getenv("REDIS_SSL", False)),
    "connection_pool": {
        "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
        "timeout": int(os.getenv("REDIS_TIMEOUT", "5")),
    },
}

# Neo4j configuration
NEO4J_CONFIG: Dict[str, Any] = {
    "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    "user": os.getenv("NEO4J_USER", "neo4j"),
    "password": os.getenv("NEO4J_PASSWORD", "password"),
    "database": os.getenv("NEO4J_DATABASE", "neo4j"),
    "max_connection_lifetime": int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600")),
    "max_connection_pool_size": int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50")),
}

# Analysis settings
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "1048576"))  # 1MB
ENABLE_SECURITY_CHECKS = bool(os.getenv("ENABLE_SECURITY_CHECKS", True))
ENABLE_TYPE_CHECKING = bool(os.getenv("ENABLE_TYPE_CHECKING", True))

# Framework detection settings
FRAMEWORK_CONFIDENCE_THRESHOLD = float(
    os.getenv("FRAMEWORK_CONFIDENCE_THRESHOLD", "0.7")
)

# Cache settings
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour

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
