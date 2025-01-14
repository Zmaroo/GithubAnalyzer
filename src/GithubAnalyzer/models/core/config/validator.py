"""Configuration validation utilities."""

from typing import Dict

from .settings import Settings


def validate_settings(settings: Settings) -> None:
    """Validate settings configuration.

    Args:
        settings: Settings instance to validate

    Raises:
        ValueError: If settings are invalid
    """
    if not isinstance(settings.analysis_settings, Dict):
        raise ValueError("analysis_settings must be a dictionary")

    required_keys = {"max_file_size", "max_files", "excluded_dirs", "excluded_files"}
    missing_keys = required_keys - set(settings.analysis_settings.keys())
    if missing_keys:
        raise ValueError(f"Missing required analysis settings: {missing_keys}")

    if not isinstance(settings.debug_mode, bool):
        raise ValueError("debug_mode must be a boolean")

    if not isinstance(settings.testing_mode, bool):
        raise ValueError("testing_mode must be a boolean")

    if not isinstance(settings.log_level, str):
        raise ValueError("log_level must be a string")
