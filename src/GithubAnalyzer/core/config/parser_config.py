"""Configuration for parsers."""
from enum import Enum
from typing import Dict, List, Optional, Union
from pathlib import Path
from .language_config import get_language_by_extension

class ConfigFormat(Enum):
    """Supported configuration file formats."""
    YAML = "yaml"
    JSON = "json"
    TOML = "toml"
    INI = "ini"

# Configuration file format mappings
CONFIG_FILE_FORMATS = {
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini"
}

# Documentation file format mappings
DOC_FILE_FORMATS: Dict[str, Dict[str, List[str]]] = {
    "markdown": {
        "extensions": [".md", ".markdown"],
        "mime_types": ["text/markdown"]
    },
    "rst": {
        "extensions": [".rst"],
        "mime_types": ["text/x-rst"]
    },
    "txt": {
        "extensions": [".txt"],
        "mime_types": ["text/plain"]
    }
}

# License file patterns
LICENSE_PATTERNS: Dict[str, List[str]] = {
    "filename_patterns": [
        "license*",
        "licence*",
        "copying*",
        "copyright*",
        "patents*"
    ],
    "content_patterns": [
        "MIT License",
        "Apache License",
        "GNU General Public License",
        "BSD License",
        "Mozilla Public License"
    ]
}

def get_parser_for_file(file_path: str | Path) -> Optional[str]:
    """Get appropriate parser for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Parser identifier or None if no parser available
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    
    # First check if it's a config file
    if extension in CONFIG_FILE_FORMATS:
        return CONFIG_FILE_FORMATS[extension]
        
    # Otherwise try to detect language
    return get_language_by_extension(extension)

def get_config_format(file_path: str) -> Optional[str]:
    """Get the specific configuration format for a file."""
    lower_path = file_path.lower()
    for format_type, info in CONFIG_FILE_FORMATS.items():
        if any(lower_path.endswith(ext) for ext in info["extensions"]):
            return format_type
    return None 