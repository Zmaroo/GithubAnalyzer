"""File handling utilities."""

import fnmatch
import os
from pathlib import Path
from typing import List, Optional

from GithubAnalyzer.config import settings


def get_file_type(file_path: str) -> Optional[str]:
    """Get the type of a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        File type string or None if not recognized
    """
    ext = os.path.splitext(file_path)[1].lower()
    type_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".go": "go",
        ".rb": "ruby",
        ".php": "php",
        ".rs": "rust",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".m": "objective-c",
        ".mm": "objective-c",
    }
    return type_map.get(ext)


def is_binary_file(file_path: str) -> bool:
    """Check if a file is binary.

    Args:
        file_path: Path to the file

    Returns:
        True if file is binary, False otherwise
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
        File size in bytes
    """
    return os.path.getsize(file_path)


def is_ignored_file(
    file_path: str, ignore_patterns: Optional[List[str]] = None
) -> bool:
    """Check if a file should be ignored based on patterns.

    Args:
        file_path: Path to the file
        ignore_patterns: Optional list of glob patterns to ignore

    Returns:
        True if file should be ignored, False otherwise
    """
    if not ignore_patterns:
        return False

    for pattern in ignore_patterns:
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def list_files(
    directory: str, ignore_patterns: Optional[List[str]] = None
) -> List[str]:
    """List all files in a directory recursively.

    Args:
        directory: Directory to list files from
        ignore_patterns: Optional list of glob patterns to ignore

    Returns:
        List of file paths
    """
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            if not is_ignored_file(file_path, ignore_patterns):
                if get_file_size(file_path) <= settings.MAX_FILE_SIZE:
                    files.append(file_path)
    return files


def ensure_directory(directory: str) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        directory: Directory path to ensure exists
    """
    Path(directory).mkdir(parents=True, exist_ok=True)
