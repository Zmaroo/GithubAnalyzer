"""Configuration settings for the application."""

from typing import Dict


class Settings:
    """Application settings container."""

    def __init__(self):
        """Initialize settings with default values."""
        self.analysis_settings: Dict[str, str] = {}
        self.debug_mode: bool = False
        self.testing_mode: bool = False
        self.log_level: str = "INFO"


settings = Settings()
