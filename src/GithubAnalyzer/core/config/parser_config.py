"""Parser-specific configurations."""

from typing import Dict, List, Optional, Union

# Configuration file format mappings
CONFIG_FILE_FORMATS: Dict[str, Dict[str, List[str]]] = {
    "yaml": {
        "extensions": [".yaml", ".yml"],
        "mime_types": ["application/x-yaml", "text/yaml"]
    },
    "json": {
        "extensions": [".json"],
        "mime_types": ["application/json"]
    },
    "toml": {
        "extensions": [".toml"],
        "mime_types": ["application/toml"]
    },
    "ini": {
        "extensions": [".ini"],
        "mime_types": ["text/plain"]
    }
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

def get_parser_for_file(file_path: str) -> Optional[str]:
    """Determine appropriate parser type for a given file.

    Args:
        file_path: Path to the file

    Returns:
        Parser type identifier or None if no appropriate parser found
    """
    lower_path = file_path.lower()
    
    # Check for config files
    for format_type, info in CONFIG_FILE_FORMATS.items():
        if any(lower_path.endswith(ext) for ext in info["extensions"]):
            return "config"
            
    # Check for documentation files
    for format_type, info in DOC_FILE_FORMATS.items():
        if any(lower_path.endswith(ext) for ext in info["extensions"]):
            return "documentation"
            
    # Check for license files
    if any(pattern in lower_path for pattern in LICENSE_PATTERNS["filename_patterns"]):
        return "license"
            
    return None

def get_config_format(file_path: str) -> Optional[str]:
    """Get the specific configuration format for a file.

    Args:
        file_path: Path to the configuration file

    Returns:
        Configuration format identifier or None if not a config file
    """
    lower_path = file_path.lower()
    for format_type, info in CONFIG_FILE_FORMATS.items():
        if any(lower_path.endswith(ext) for ext in info["extensions"]):
            return format_type
    return None 