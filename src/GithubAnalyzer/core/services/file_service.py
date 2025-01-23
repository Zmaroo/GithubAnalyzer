"""File service for handling file operations."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from tree_sitter_language_pack import get_language

from ..models.errors import FileOperationError, LanguageError
from ..models.file import FileInfo, FileFilterConfig
from ..config.settings import settings

logger = logging.getLogger(__name__)

# Common file extensions and their corresponding languages
EXTENSION_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.cpp': 'cpp',
    '.c': 'c',
    '.h': 'c',
    '.hpp': 'cpp',
    '.java': 'java',
    '.rb': 'ruby',
    '.go': 'go',
    '.rs': 'rust',
    '.php': 'php',
    '.cs': 'c_sharp',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.m': 'objective-c',
    '.mm': 'objective-cpp'
}

class FileService:
    """Service for file operations."""

    def list_files(self, root_path: Path, filter_config: Optional[FileFilterConfig] = None) -> List[FileInfo]:
        """List files in a directory, optionally filtered by configuration."""
        if not root_path.exists():
            raise FileOperationError(f"Path does not exist: {root_path}")
        if not root_path.is_dir():
            raise FileOperationError(f"Path is not a directory: {root_path}")

        files = []
        try:
            for path in root_path.rglob('*'):
                if path.is_file():
                    try:
                        file_info = self._create_file_info(path)
                        if filter_config is None or filter_config.matches(file_info):
                            files.append(file_info)
                    except Exception as e:
                        logger.warning(f"Failed to process file {path}: {str(e)}")
        except Exception as e:
            raise FileOperationError(f"Failed to list files in {root_path}: {str(e)}")

        return files

    def _create_file_info(self, path: Path) -> FileInfo:
        """Create a FileInfo instance for a file."""
        try:
            language = self._detect_language(path)
            metadata = {
                'size': path.stat().st_size,
                'extension': path.suffix,
                'is_binary': self._is_binary(path)
            }
            return FileInfo(path=path, language=language, metadata=metadata)
        except Exception as e:
            raise FileOperationError(f"Failed to create file info for {path}: {str(e)}")

    def _detect_language(self, path: Path) -> str:
        """Detect the language of a file based on its extension."""
        extension = path.suffix.lower()
        language = EXTENSION_MAP.get(extension, 'unknown')
        
        # Verify the language is supported by tree-sitter
        if language != 'unknown':
            try:
                get_language(language)
            except LookupError:
                logger.warning(f"Language {language} is not supported by tree-sitter")
                language = 'unknown'
            
        return language

    def get_file_info(self, file_path: Path) -> FileInfo:
        """Get file information.
        
        Args:
            file_path: Path to file
            
        Returns:
            FileInfo object
            
        Raises:
            FileOperationError: If file operation fails
            LanguageError: If language is not supported
        """
        try:
            if not file_path.exists():
                raise FileOperationError(f"File not found: {file_path}")
                
            language = self._detect_language(file_path)
            if language == "unknown":
                raise LanguageError(f"Language not supported: {file_path}")
                
            metadata = {
                'size': file_path.stat().st_size,
                'extension': file_path.suffix,
                'is_binary': self._is_binary(file_path)
            }
            return FileInfo(path=file_path, language=language, metadata=metadata)
            
        except LanguageError:
            raise
        except Exception as e:
            raise FileOperationError(f"Failed to get file info: {str(e)}")

    def _is_binary(self, file_path: Path) -> bool:
        """Check if file is binary.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is binary, False otherwise
        """
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except Exception:
            return False

    def read_file(self, file_path: Path) -> str:
        """Read file contents.
        
        Args:
            file_path: Path to file
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError if file doesn't exist
            IOError if file can't be read
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error("Failed to read %s: %s", file_path, e)
            raise

    def get_required_config_fields(self) -> List[str]:
        """Get required configuration fields."""
        return ["root_dir", "exclude_patterns", "include_patterns"] 

    def test_file_type(self, file_info: FileInfo, expected_type: str) -> bool:
        """Test if file matches expected type."""
        if isinstance(file_info.language, str):
            return file_info.language == expected_type
        return str(file_info.language) == expected_type 