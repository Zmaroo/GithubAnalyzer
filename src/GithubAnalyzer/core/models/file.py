"""File-related data models."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional


class FileType(Enum):
    """Enumeration of supported file types."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    CSS = "css"
    YAML = "yaml"
    JSON = "json"
    BASH = "bash"
    CPP = "cpp"
    JAVA = "java"
    HTML = "html"
    UNKNOWN = "unknown"


@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    file_type: FileType
    size: int
    is_binary: bool
    mime_type: Optional[str] = None
    encoding: str = "utf-8"

    @property
    def extension(self) -> str:
        """Get file extension."""
        return self.path.suffix.lower()

    @property
    def name(self) -> str:
        """Get file name."""
        return self.path.name


@dataclass
class FilePattern:
    """File pattern for matching files."""
    pattern: str
    is_regex: bool = False
    case_sensitive: bool = False


@dataclass
class FileFilterConfig:
    """Configuration for file filtering."""
    include_patterns: List[FilePattern]
    exclude_patterns: List[FilePattern]
    max_size: int
    allowed_types: List[FileType] 