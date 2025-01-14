"""Utilities for file operations and type detection."""

import os
from typing import Optional


def get_file_type(file_path: str) -> Optional[str]:
    """Get the type of a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        File type string or None if not recognized
    """
    extension = os.path.splitext(file_path)[1].lower()

    type_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".scala": "scala",
        ".kt": "kotlin",
        ".swift": "swift",
        ".m": "objective-c",
        ".r": "r",
        ".sh": "shell",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".md": "markdown",
        ".rst": "restructuredtext",
        ".xml": "xml",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
    }

    return type_map.get(extension)


def is_binary_file(file_path: str) -> bool:
    """Check if a file is binary.

    Args:
        file_path: Path to the file

    Returns:
        True if the file is binary, False otherwise
    """
    try:
        with open(file_path, "tr") as f:
            f.read(1024)
            return False
    except UnicodeDecodeError:
        return True


def get_file_size(file_path: str) -> int:
    """Get the size of a file in bytes.

    Args:
        file_path: Path to the file

    Returns:
        Size of the file in bytes
    """
    return os.path.getsize(file_path)


def is_ignored_file(file_path: str, ignore_patterns: list[str]) -> bool:
    """Check if a file should be ignored based on patterns.

    Args:
        file_path: Path to the file
        ignore_patterns: List of glob patterns to ignore

    Returns:
        True if the file should be ignored, False otherwise
    """
    from fnmatch import fnmatch

    normalized_path = os.path.normpath(file_path)
    return any(fnmatch(normalized_path, pattern) for pattern in ignore_patterns)
