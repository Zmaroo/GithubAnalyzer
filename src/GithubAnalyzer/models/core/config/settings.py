"""Settings model."""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Settings:
    """Application settings."""
    parser_timeout: int = 5000
    max_parse_size: int = 5242880
    debug_mode: bool = False
    testing_mode: bool = False
    log_level: str = "INFO"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create settings from dictionary."""
        return cls(**data) 