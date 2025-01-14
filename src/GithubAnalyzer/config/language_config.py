"""Language configuration and mappings."""

from typing import Dict, List, Set

# Tree-sitter supported languages and their file extensions
TREE_SITTER_LANGUAGES = {
    # Core languages
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "java": ".java",
    "cpp": ".cpp",
    "c": ".c",
    "rust": ".rs",
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
    "csharp": ".cs",
    "scala": ".scala",
    "kotlin": ".kt",
    "lua": ".lua",
    "toml": ".toml",
    "xml": ".xml",
    "markdown": ".md",
    "sql": ".sql",
    "arduino": ".ino",
    "cmake": "CMakeLists.txt",
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
