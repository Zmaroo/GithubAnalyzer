"""File utility functions."""

import os
import fnmatch
from pathlib import Path
from typing import List, Optional, Union

from ..models.core.errors import FileOperationError
from ..config import settings
from ..config.language_config import PARSER_LANGUAGE_MAP


def get_file_type(file_path: str) -> Optional[str]:
    """Get the language type from file extension."""
    ext = Path(file_path).suffix.lower()
    
    # Map extensions to languages
    extension_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.css': 'css',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.sh': 'bash',
        '.cpp': 'cpp',
        '.java': 'java',
        '.html': 'html',
    }
    
    return extension_map.get(ext)


def is_binary_file(file_path: str) -> bool:
    """Check if file is binary.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if file is binary, False otherwise
    """
    try:
        # Read first chunk in binary mode
        chunk_size = 8192  # Typical disk block size
        with open(file_path, 'rb') as f:
            chunk = f.read(chunk_size)
        
        # Try to decode as text
        chunk.decode('utf-8')
        return False
    except UnicodeDecodeError:
        return True
    except Exception as e:
        raise FileOperationError(f"Error checking if file is binary: {str(e)}")


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
    """Check if file should be ignored."""
    if ignore_patterns is None:
        ignore_patterns = ["*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", "*.dylib"]
    
    basename = os.path.basename(file_path)
    return any(fnmatch.fnmatch(basename, pattern) for pattern in ignore_patterns)


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


def validate_file_path(file_path: Union[str, Path]) -> Path:
    """Validate and normalize file path.
    
    Args:
        file_path: Path to validate
        
    Returns:
        Normalized Path object
        
    Raises:
        FileOperationError: If path is invalid
    """
    try:
        if isinstance(file_path, str):
            path = Path(file_path)
        else:
            path = file_path
        
        # Resolve to absolute path
        path = path.resolve()
        
        return path
    except Exception as e:
        raise FileOperationError(f"Invalid file path: {file_path} - {str(e)}")


def get_parser_language(file_path: str) -> Optional[str]:
    """Get the parser language for a file."""
    file_type = get_file_type(file_path)
    return PARSER_LANGUAGE_MAP.get(file_type)


def validate_source_file(file_path: Union[str, Path]) -> Path:
    """Validate a source file for parsing."""
    path = validate_file_path(file_path)
    if not path.exists():
        raise FileOperationError(f"File not found: {path}")
    if is_binary_file(str(path)):
        raise FileOperationError(f"Cannot parse binary file: {path}")
    return path
