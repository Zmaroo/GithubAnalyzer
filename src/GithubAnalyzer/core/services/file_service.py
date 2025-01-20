"""File service for handling file operations."""

import mimetypes
import os
import fnmatch
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..models.errors import FileOperationError, ConfigError
from ..models.file import FileInfo, FileType, FileFilterConfig
from .base_service import BaseService


class FileService(BaseService):
    """Service for file operations."""

    def __init__(self, filter_config: Optional[FileFilterConfig] = None):
        """Initialize file service.
        
        Args:
            filter_config: Optional configuration for file filtering
        """
        super().__init__()
        self._filter_config = filter_config
        self._binary_signatures: Set[bytes] = {
            b'\x7fELF',  # Unix executables
            b'MZ',       # Windows executables
            b'\x89PNG',  # PNG images
            b'GIF',      # GIF images
            b'\xFF\xD8', # JPEG images
        }

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            The validated configuration dictionary
            
        Raises:
            ConfigError: If configuration is invalid
        """
        # No config needed for file service
        return config

    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize the file service.
        
        Args:
            languages: Not used by file service
        """
        self._initialized = True

    def cleanup(self) -> None:
        """Clean up file service resources."""
        self._initialized = False

    def get_file_info(self, file_path: str | Path) -> FileInfo:
        """Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileInfo object containing file metadata
            
        Raises:
            FileOperationError: If file cannot be accessed
        """
        try:
            path = Path(file_path).resolve()
            if not path.exists():
                raise FileOperationError(f"File not found: {path}")
            
            return FileInfo(
                path=path,
                file_type=self._detect_file_type(path),
                size=path.stat().st_size,
                is_binary=self._is_binary(path)
            )
        except Exception as e:
            raise FileOperationError(f"Error getting file info: {str(e)}")

    def list_files(self, directory: str | Path) -> List[FileInfo]:
        """List all files in a directory recursively.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of FileInfo objects for each file
            
        Raises:
            FileOperationError: If directory cannot be accessed
        """
        try:
            files = []
            directory = Path(directory).resolve()
            
            for root, _, filenames in os.walk(str(directory)):
                for filename in filenames:
                    file_path = Path(root) / filename
                    try:
                        file_info = self.get_file_info(file_path)
                        if self._should_include_file(file_info):
                            files.append(file_info)
                    except FileOperationError:
                        self.logger.warning(f"Skipping inaccessible file: {file_path}")
                        
            return files
        except Exception as e:
            raise FileOperationError(f"Error listing files: {str(e)}")

    def _detect_file_type(self, file_path: Path) -> FileType:
        """Detect file type from extension and content."""
        ext = file_path.suffix.lower()
        
        # Map extensions to FileType
        extension_map = {
            '.py': FileType.PYTHON,
            '.js': FileType.JAVASCRIPT,
            '.ts': FileType.TYPESCRIPT,
            '.css': FileType.CSS,
            '.yaml': FileType.YAML,
            '.yml': FileType.YAML,
            '.json': FileType.JSON,
            '.sh': FileType.BASH,
            '.cpp': FileType.CPP,
            '.java': FileType.JAVA,
            '.html': FileType.HTML
        }
        
        return extension_map.get(ext, FileType.UNKNOWN)

    def _is_binary(self, file_path: Path) -> bool:
        """Check if file is binary."""
        try:
            # Check file signature
            with open(file_path, 'rb') as f:
                signature = f.read(4)
                if any(signature.startswith(sig) for sig in self._binary_signatures):
                    return True
            
            # Try reading as text
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)
            return False
        except UnicodeDecodeError:
            return True
        except Exception as e:
            raise FileOperationError(f"Error checking if file is binary: {str(e)}")

    def _should_include_file(self, file_info: FileInfo) -> bool:
        """Check if file should be included based on filter config."""
        if not self._filter_config:
            return True
            
        # Check file size
        if file_info.size > self._filter_config.max_size:
            return False
            
        # Check file type
        if (self._filter_config.allowed_types and 
            file_info.file_type not in self._filter_config.allowed_types):
            return False
            
        # Check patterns
        name = str(file_info.path)
        
        # Check exclude patterns first
        for pattern in self._filter_config.exclude_patterns:
            if self._matches_pattern(name, pattern):
                return False
                
        # If we have include patterns, file must match at least one
        if self._filter_config.include_patterns:
            return any(
                self._matches_pattern(name, pattern)
                for pattern in self._filter_config.include_patterns
            )
            
        return True

    def _matches_pattern(self, name: str, pattern: str) -> bool:
        """Check if filename matches pattern."""
        if not pattern.case_sensitive:
            name = name.lower()
            pattern = pattern.lower()
            
        if pattern.is_regex:
            return bool(re.match(pattern, name))
        return fnmatch.fnmatch(name, pattern) 