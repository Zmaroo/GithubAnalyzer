"""Application settings."""

from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path

@dataclass
class Settings:
    """Application settings."""
    parser_timeout: int = 5000
    debug_mode: bool = False
    testing_mode: bool = False
    log_level: str = "INFO"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create settings from dictionary."""
        return cls(**data)

# Global settings instance
settings = Settings()

# Constants
BASE_DIR = Path(__file__).parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
DEBUG_MODE = False
TESTING_MODE = False
ENV = "development"
LOG_LEVEL = "INFO"
PARSER_TIMEOUT = 5000  # milliseconds

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "default": {
            "level": LOG_LEVEL,
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": LOG_LEVEL,
            "propagate": True
        }
    }
}
