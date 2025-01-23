"""File-related data models."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Any, Dict
from tree_sitter_language_pack import installed_bindings_map

@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    language: str
    metadata: Optional[Dict[str, Any]] = None

    @property
    def file_type(self) -> str:
        """Get language identifier from tree-sitter-language-pack."""
        return self.language

    def __str__(self) -> str:
        """Get string representation."""
        return str(self.path)

    @property
    def extension(self) -> str:
        """Get file extension."""
        return self.path.suffix.lower()

    @property
    def name(self) -> str:
        """Get file name."""
        return self.path.name

    def __eq__(self, other: Any) -> bool:
        """Compare file info objects."""
        if isinstance(other, str):
            return self.language == other
        if isinstance(other, FileInfo):
            return (self.path == other.path and 
                   self.language == other.language and
                   self.metadata == other.metadata)
        return False


@dataclass
class FilePattern:
    """File pattern for matching files."""
    pattern: str
    is_regex: bool = False
    case_sensitive: bool = False


@dataclass
class FileFilterConfig:
    """Configuration for filtering files."""
    include_languages: Optional[List[str]] = None
    exclude_languages: Optional[List[str]] = None
    include_paths: Optional[List[str]] = None
    exclude_paths: Optional[List[str]] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None

    def matches(self, file_info: FileInfo) -> bool:
        """Check if a file matches the filter configuration."""
        if self.include_languages and file_info.language not in self.include_languages:
            return False
        if self.exclude_languages and file_info.language in self.exclude_languages:
            return False
        if self.include_paths and not any(str(file_info.path).startswith(p) for p in self.include_paths):
            return False
        if self.exclude_paths and any(str(file_info.path).startswith(p) for p in self.exclude_paths):
            return False
        return True 