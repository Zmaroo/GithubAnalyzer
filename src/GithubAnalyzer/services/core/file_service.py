"""File service for GithubAnalyzer."""
import os
from pathlib import Path
from typing import List, Optional, Union

from GithubAnalyzer.utils.logging.logging_config import get_logger
from GithubAnalyzer.models.core.file import FileInfo, FileFilterConfig

logger = get_logger(__name__)

# Common file extensions and their corresponding languages
LANGUAGE_EXTENSIONS = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.java': 'Java',
    '.cpp': 'C++',
    '.c': 'C',
    '.h': 'C',
    '.hpp': 'C++',
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.m': 'Objective-C',
    '.mm': 'Objective-C++',
}

class FileService:
    """Service for file operations."""
    
    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """Initialize the file service.
        
        Args:
            base_path: Optional base path for file operations. Defaults to the current directory.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        logger.debug({
            "message": "FileService initialized",
            "context": {
                "base_path": str(self.base_path)
            }
        })
        
    def list_files(self, root_path: Path, filter_config: Optional[FileFilterConfig] = None) -> List[FileInfo]:
        """List files in a directory, optionally filtered by configuration.
        
        Args:
            root_path: Root directory to start searching from.
            filter_config: Optional configuration for filtering files.
            
        Returns:
            List of FileInfo objects for matching files.
            
        Raises:
            FileNotFoundError: If the root path does not exist.
            PermissionError: If a directory cannot be accessed.
        """
        try:
            files = []
            for file_path in root_path.rglob('*'):
                if not file_path.is_file():
                    continue
                    
                if filter_config and not self._matches_filter(file_path, filter_config):
                    continue
                    
                file_info = FileInfo(
                    path=file_path,
                    language=self._detect_language(file_path),
                    size=file_path.stat().st_size,
                    modified=file_path.stat().st_mtime
                )
                files.append(file_info)
                
            logger.debug({
                "message": "Files listed successfully",
                "context": {
                    "root_path": str(root_path),
                    "filter_config": filter_config.__dict__ if filter_config else None,
                    "file_count": len(files)
                }
            })
            return files
            
        except (FileNotFoundError, PermissionError) as e:
            logger.error({
                "message": "Error listing files",
                "context": {
                    "root_path": str(root_path),
                    "filter_config": filter_config.__dict__ if filter_config else None,
                    "error": str(e)
                }
            })
            raise
            
    def read_file(self, file_path: Union[str, Path]) -> str:
        """Read the contents of a file.
        
        Args:
            file_path: Path to the file to read.
            
        Returns:
            The contents of the file as a string.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
        """
        try:
            full_path = self.base_path / file_path
            with open(full_path, 'r') as f:
                content = f.read()
                
            logger.debug({
                "message": "File read successfully",
                "context": {
                    "file_path": str(file_path),
                    "size_bytes": len(content)
                }
            })
            return content
            
        except (FileNotFoundError, PermissionError) as e:
            logger.error({
                "message": "Error reading file",
                "context": {
                    "file_path": str(file_path),
                    "error": str(e)
                }
            })
            raise
            
    def write_file(self, file_path: Union[str, Path], content: str) -> None:
        """Write content to a file.
        
        Args:
            file_path: Path to the file to write.
            content: Content to write to the file.
            
        Raises:
            PermissionError: If the file cannot be written.
            OSError: If the directory does not exist.
        """
        try:
            full_path = self.base_path / file_path
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)
                
            logger.debug({
                "message": "File written successfully",
                "context": {
                    "file_path": str(file_path),
                    "size_bytes": len(content)
                }
            })
            
        except (PermissionError, OSError) as e:
            logger.error({
                "message": "Error writing file",
                "context": {
                    "file_path": str(file_path),
                    "error": str(e)
                }
            })
            raise
            
    def _matches_filter(self, file_path: Path, filter_config: FileFilterConfig) -> bool:
        """Check if a file matches the filter configuration.
        
        Args:
            file_path: Path to the file to check.
            filter_config: Configuration for filtering files.
            
        Returns:
            True if the file matches the filter, False otherwise.
        """
        if filter_config.exclude_patterns:
            for pattern in filter_config.exclude_patterns:
                if file_path.match(pattern):
                    return False
                    
        if filter_config.include_patterns:
            for pattern in filter_config.include_patterns:
                if file_path.match(pattern):
                    return True
            return False
            
        return True
        
    def _detect_language(self, file_path: Path) -> str:
        """Detect the programming language of a file based on its extension.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            The detected programming language, or 'Unknown' if not recognized.
        """
        extension = file_path.suffix.lower()
        return LANGUAGE_EXTENSIONS.get(extension, 'Unknown')
        
    def validate_language(self, file_info: FileInfo, expected_type: str) -> bool:
        """Validate that a file is of the expected language type.
        
        Args:
            file_info: FileInfo object to validate.
            expected_type: Expected language type.
            
        Returns:
            True if the file matches the expected type, False otherwise.
        """
        if isinstance(file_info.language, str):
            return file_info.language == expected_type
        return str(file_info.language) == expected_type 