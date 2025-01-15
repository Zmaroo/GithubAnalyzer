"""Language configuration and mappings."""

from typing import Dict, List, Set, Tuple

# Tree-sitter language variants
LANGUAGE_VARIANTS = {
    "typescript": ["typescript", "tsx"],
    "javascript": ["javascript", "jsx"],
}

# Tree-sitter supported languages and their file extensions
TREE_SITTER_LANGUAGES = {
    # Core languages
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "tsx": ".tsx",
    "jsx": ".jsx",
    "java": ".java",
    "cpp": ".cpp",
    "c": ".c",
    "go": ".go",
    "ruby": ".rb",
    # Web languages
    "html": ".html",
    "css": ".css",
    "json": ".json",
    "yaml": ".yaml",
    # Shell languages
    "bash": ".sh",
    # Additional languages
    "php": ".php",
    "c-sharp": ".cs",
    "scala": ".scala",
    "kotlin": ".kt",
    "lua": ".lua",
    "toml": ".toml",
    "xml": ".xml",
    "markdown": ".md",
    "sql": ".sql",
    "arduino": ".ino",
    "cuda": ".cu",
    "groovy": ".groovy",
    "matlab": ".m",
}

# Special file mappings for non-code files
SPECIAL_FILE_MAPPINGS = {
    # Config files
    ".yaml": "config",
    ".yml": "config",
    ".json": "config",
    ".toml": "config",
    # Documentation files
    ".md": "documentation",
    ".rst": "documentation",
    ".txt": "documentation",
    # License files
    "LICENSE": "license",
    "LICENSE.md": "license",
    "LICENSE.txt": "license",
}


def get_file_type_mapping() -> Dict[str, str]:
    """Get complete file type to parser mapping."""
    mapping = {}

    # Add tree-sitter mappings
    for ext in TREE_SITTER_LANGUAGES.values():
        mapping[ext] = "tree-sitter"

    # Add special file mappings
    mapping.update(SPECIAL_FILE_MAPPINGS)

    return mapping


def get_supported_languages() -> Set[str]:
    """Get set of supported languages."""
    return set(TREE_SITTER_LANGUAGES.keys())


def get_language_by_extension(extension: str) -> str:
    """Get language name from file extension."""
    for lang, ext in TREE_SITTER_LANGUAGES.items():
        if ext == extension:
            return lang
    raise ValueError(f"Unsupported file extension: {extension}")


def get_language_variant(lang: str) -> Tuple[str, str]:
    """Get language variant name if applicable.
    
    Args:
        lang: Base language name
        
    Returns:
        Tuple of (module_name, variant_name)
    """
    if lang in ["tsx", "jsx"]:
        return (
            f"tree_sitter_{lang.replace('sx', '')}",  # module name
            lang  # variant name
        )
    return (f"tree_sitter_{lang}", "")  # No variant
