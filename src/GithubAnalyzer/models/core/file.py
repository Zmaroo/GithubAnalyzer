from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
"""File-related data models."""

from pathlib import Path

from GithubAnalyzer.services.analysis.parsers.language_service import LanguageService

@dataclass
class FileInfo:
    """Information about a file in the repository."""
    path: Path
    language: str
    repo_id: int
    metadata: Optional[Dict[str, Any]] = None
    is_supported: bool = True

    def __post_init__(self):
        """Validate file information after initialization."""
        # Use LanguageService to validate the language
        language_service = LanguageService()
        
        # Handle special cases first
        filename = self.path.name.lower()
        if filename == "license" or filename == "license.txt":
            self.language = "plaintext"
            self.is_supported = False
            return
            
        # Get language from service
        try:
            detected_language = language_service.get_language_for_file(str(self.path))
            if detected_language == 'plaintext':
                self.is_supported = False
            self.language = detected_language
        except Exception as e:
            self.language = 'plaintext'
            self.is_supported = False

    def update(self, *args, **kwargs) -> None:
        """Update FileInfo attributes.
        
        Args:
            *args: Positional arguments to update attributes in order: path, language, metadata, is_supported
            **kwargs: Keyword arguments to update specific attributes
            
        Raises:
            AttributeError: If trying to update a non-existent attribute
            ValueError: If too many positional arguments are provided
        """
        # Handle positional arguments
        if args:
            attrs = ['path', 'language', 'metadata', 'is_supported']
            if len(args) > len(attrs):
                raise ValueError(f"Too many positional arguments. Expected at most {len(attrs)}, got {len(args)}")
            for attr, value in zip(attrs, args):
                setattr(self, attr, value)
        
        # Handle keyword arguments
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"FileInfo has no attribute '{key}'")

    def __str__(self) -> str:
        """Return string representation."""
        return f"FileInfo(path={self.path}, language={self.language})"

    def __eq__(self, other: object) -> bool:
        """Compare two FileInfo objects."""
        if not isinstance(other, FileInfo):
            return NotImplemented
        return self.path == other.path and self.language == other.language

    @property
    def file_type(self) -> str:
        """Get the file type based on extension."""
        return self.path.suffix.lstrip('.') if self.path.suffix else ''

    @property
    def extension(self) -> str:
        """Get the file extension."""
        return self.path.suffix

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
        if self.include_paths:
            matches = False
            for pattern in self.include_paths:
                if file_info.path.match(pattern):
                    matches = True
                    break
            if not matches:
                return False
        if self.exclude_paths:
            for pattern in self.exclude_paths:
                if file_info.path.match(pattern):
                    return False
        return True 