"""File service for GithubAnalyzer."""
import os
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import git

from GithubAnalyzer.models.core.file import FileFilterConfig, FileInfo
from GithubAnalyzer.services.parsers.core.custom_parsers import (
    CustomParser, EditorConfigParser, EnvFileParser, GitignoreParser,
    LockFileParser, RequirementsParser, get_custom_parser)
from GithubAnalyzer.services.analysis.parsers.language_service import \
    LanguageService
from GithubAnalyzer.services.analysis.parsers.query_patterns import \
    SPECIAL_FILENAMES
from GithubAnalyzer.services.core.base_service import BaseService
from GithubAnalyzer.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Git-related files and directories to exclude
GIT_EXCLUDES: Set[str] = {
    '.git',
    '.gitignore',
    '.gitattributes',
    '.gitmodules',
    '.github',
    '.gitkeep'
}

# Build and cache directories to exclude
BUILD_EXCLUDES: Set[str] = {
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    'build',
    'dist',
    'node_modules',
    '.env',
    '.venv',
    'env',
    'venv',
    'ENV',
    '.tox',
    '.pytest_cache',
    '.hypothesis',
    'target',
    'Debug',
    'Release',
    'cmake-build-*',
    '.gradle',
    '.m2',
    '.cargo',
    '.npm',
    '.yarn',
    'bower_components',
    '.pub-cache',
    '.nuget',
    'tmp',
    'temp',
    'cache',
    'logs',
    'log',
    '.ipynb_checkpoints',
    '.terraform',
    '.serverless',
    '.next',
    '.parcel-cache',
    '.cache',
    '.pytest_cache',
    '__snapshots__',
    '.nyc_output',
    '.docusaurus',
    '.turbo',
    '.svelte-kit',
    '.astro',
    '.vercel',
    '.netlify',
    '.firebase',
    '.angular',
    '.quasar',
    '.umi',
    '.rpt2_cache',
    '.rts2_cache',
    '.fusion',
    '.now',
    '.serverless',
    '.webpack',
    '.dynamodb'
}

# Editor and IDE files to exclude
EDITOR_EXCLUDES: Set[str] = {
    '.idea',
    '.vscode',
    '*.swp',
    '*.swo',
    '*~',
    '.DS_Store',
    'Thumbs.db',
    '.vs',
    '.settings',
    '.project',
    '.classpath',
    '*.iml',
    '*.ipr',
    '*.iws',
    '*.suo',
    '*.user',
    '*.dbmdl',
    '*.jfm',
    '.sublime-project',
    '.sublime-workspace',
    '*.sublime-*',
    '.atom',
    '.brackets.json',
    '.komodoproject',
    '*.komodoproject',
    '.komodotools',
    '.netbeans',
    'nbproject',
    '.eclipse',
    '.buildpath',
    '.tm_properties',
    '.tern-project',
    '.tags',
    '.tags_sorted_by_file',
    '.gemtags',
    '.ctags',
    '.rgignore',
    '.agignore',
    '.ignore',
    '.ac-php-conf.json',
    '.dir-locals.el',
    '*.code-workspace',
    '.history',
    '.ionide'
}

# Combine all excludes
DEFAULT_EXCLUDES: Set[str] = GIT_EXCLUDES | BUILD_EXCLUDES | EDITOR_EXCLUDES

@dataclass
class FileService(BaseService):
    """Service for managing repository files."""
    base_path: Optional[Path] = None
    _language_service: LanguageService = field(default_factory=LanguageService)
    _filter_config: FileFilterConfig = field(default_factory=FileFilterConfig)
    _start_time: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Initialize the service."""
        super().__post_init__()
        
        self._log("debug", "File service initialized",
                operation="initialization",
                base_path=str(self.base_path) if self.base_path else None)
        
    def clone_repository(self, repo_url: str) -> Optional[Path]:
        """Clone or get local repository path.
        
        Args:
            repo_url: URL of the repository to clone or local file path
            
        Returns:
            Path to the repository directory, or None if cloning failed
        """
        try:
            potential_path = None
            # If repo_url starts with 'file://' or exists as a path on disk, treat it as a local repository
            if repo_url.startswith('file://'):
                potential_path = Path(repo_url.replace('file://', ''))
            elif Path(repo_url).exists():
                potential_path = Path(repo_url)
            
            if potential_path is not None:
                # Traverse upward to check if the directory is part of a Git repository
                current = potential_path
                while current.parent != current:
                    if (current / '.git').exists():
                        return potential_path
                    current = current.parent
                self._log("warning", f"Local repository '{potential_path}' is not a git repository; proceeding with analysis.")
                return potential_path
            else:
                # If not a local path, assume it's a remote git URL and clone it
                with tempfile.TemporaryDirectory() as temp_dir:
                    git.Repo.clone_from(repo_url, temp_dir)
                    return Path(temp_dir)
                    
        except Exception as e:
            self._log("error", "Failed to clone repository",
                     repo_url=repo_url,
                     error=str(e))
            return None
        
    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """Get standard context for logging.
        
        Args:
            **kwargs: Additional context key-value pairs
            
        Returns:
            Dict with standard context fields plus any additional fields
        """
        context = {
            'module': 'file',
            'thread': threading.get_ident(),
            'duration_ms': (time.time() - self._start_time) * 1000,
            'base_path': str(self.base_path) if self.base_path else None
        }
        context.update(kwargs)
        return context
        
    def _log(self, level: str, message: str, **kwargs) -> None:
        """Log with consistent context.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Message to log
            **kwargs: Additional context key-value pairs
        """
        context = self._get_context(**kwargs)
        getattr(self._logger, level)(message, extra={'context': context})

    def get_repository_files(self, repo_path: Union[str, Path], repo_id: Optional[int] = None) -> List[FileInfo]:
        """Get all files from a repository directory.
        
        Args:
            repo_path: Path to the repository directory
            repo_id: Optional repository ID to associate with files
            
        Returns:
            List of FileInfo objects for each file
        """
        repo_path = Path(repo_path)
        
        # Find repository root (directory containing .git)
        repo_root = repo_path
        while repo_root.parent != repo_root:
            if (repo_root / '.git').exists():
                break
            repo_root = repo_root.parent
            
        self._log("debug", "Found repository root",
                 repo_path=str(repo_path),
                 repo_root=str(repo_root))
        
        # Use custom filter config for repository files
        filter_config = FileFilterConfig(
            exclude_paths=list(GIT_EXCLUDES | BUILD_EXCLUDES | EDITOR_EXCLUDES)
        )
        self._log("debug", "Created filter config",
                 exclude_paths=filter_config.exclude_paths)
        
        return self.list_files(repo_path, filter_config, repo_id)
        
    def list_files(self, root_path: Path, filter_config: Optional[FileFilterConfig] = None, repo_id: Optional[int] = None) -> List[FileInfo]:
        """List files in a directory, optionally filtered by configuration.
        
        Args:
            root_path: Root directory to start searching from.
            filter_config: Optional configuration for filtering files.
            repo_id: Optional repository ID to associate with files.
            
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
                    
                # Skip files based on filter config
                if filter_config and not self._matches_filter(file_path, filter_config):
                    self._log("debug", "File filtered out by config", file=str(file_path))
                    continue
                
                # Skip binary files early
                if self._is_binary_file(file_path):
                    self._log("debug", "Skipping binary file", file=str(file_path))
                    continue
                
                # Get language from LanguageService
                language = self._detect_language(file_path)
                self._log("debug", "Detected language", file=str(file_path), language=language)
                
                # Create FileInfo with detected language
                file_info = FileInfo(
                    path=file_path,
                    language=language,
                    repo_id=repo_id or 0,  # Use 0 as default if no repo_id provided
                    metadata={
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime,
                        'is_special': file_path.name in SPECIAL_FILENAMES
                    }
                )
                self._log("debug", "Created FileInfo", file=str(file_path), language=language, is_supported=file_info.is_supported)
                files.append(file_info)
                
            self._log("debug", "Files listed successfully",
                     root_path=str(root_path),
                     filter_config=filter_config.__dict__ if filter_config else None,
                     file_count=len(files))
            return files
            
        except (FileNotFoundError, PermissionError) as e:
            self._log("error", "Error listing files",
                     root_path=str(root_path),
                     filter_config=filter_config.__dict__ if filter_config else None,
                     error=str(e))
            raise
            
    def _is_binary_file(self, file_path: Union[str, Path]) -> bool:
        """Check if a file is binary.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if the file is binary, False otherwise.
        """
        try:
            with open(file_path, 'rb') as f:
                # Read first 8000 bytes
                chunk = f.read(8000)
                # Count null bytes
                null_count = chunk.count(b'\x00')
                # If more than 10% of bytes are null, consider it binary
                return null_count > len(chunk) * 0.1
        except (FileNotFoundError, PermissionError):
            return False
            
    def read_file(self, file_path: Union[str, Path]) -> str:
        """Read the contents of a file.
        
        Args:
            file_path: Path to the file to read.
            
        Returns:
            The contents of the file as a string.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read.
            ValueError: If the file is binary.
        """
        try:
            full_path = self.base_path / file_path
            
            # Check if file is binary
            if self._is_binary_file(full_path):
                self._log("debug", "Skipping binary file",
                         file_path=str(file_path))
                raise ValueError("Cannot read binary file")
                
            with open(full_path, 'r') as f:
                content = f.read()
                
            self._log("debug", "File read successfully",
                     file_path=str(file_path),
                     size_bytes=len(content))
            return content
            
        except (FileNotFoundError, PermissionError) as e:
            self._log("error", "Error reading file",
                     file_path=str(file_path),
                     error=str(e))
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
                
            self._log("debug", "File written successfully",
                     file_path=str(file_path),
                     size_bytes=len(content))
            
        except (PermissionError, OSError) as e:
            self._log("error", "Error writing file",
                     file_path=str(file_path),
                     error=str(e))
            raise
            
    def _matches_filter(self, file_path: Path, filter_config: FileFilterConfig) -> bool:
        """Check if a file matches the filter configuration.
        
        Args:
            file_path: Path to the file to check.
            filter_config: Configuration for filtering files.
            
        Returns:
            True if the file matches the filter, False otherwise.
        """
        if filter_config.exclude_paths:
            for pattern in filter_config.exclude_paths:
                # Check if pattern is a full path pattern (contains '/')
                if '/' in pattern:
                    if file_path.match(pattern):
                        self._log("debug", "File excluded by path pattern",
                                file=str(file_path),
                                pattern=pattern,
                                reason="full path match")
                        return False
                else:
                    # For simple patterns, only match against the file name
                    if file_path.name == pattern or file_path.name.startswith('.'):
                        self._log("debug", "File excluded by name pattern",
                                file=str(file_path),
                                pattern=pattern,
                                reason="exact name match or dot file")
                        return False
                    # For wildcard patterns, match against the file name
                    if '*' in pattern and file_path.name.endswith(pattern.replace('*', '')):
                        self._log("debug", "File excluded by wildcard pattern",
                                file=str(file_path),
                                pattern=pattern,
                                reason="wildcard match")
                        return False
                    
        if filter_config.include_paths:
            for pattern in filter_config.include_paths:
                # Check if pattern is a full path pattern (contains '/')
                if '/' in pattern:
                    if file_path.match(pattern):
                        self._log("debug", "File included by path pattern",
                                file=str(file_path),
                                pattern=pattern,
                                reason="full path match")
                        return True
                else:
                    # For simple patterns, only match against the file name
                    if file_path.name == pattern:
                        self._log("debug", "File included by name pattern",
                                file=str(file_path),
                                pattern=pattern,
                                reason="exact name match")
                        return True
                    # For wildcard patterns, match against the file name
                    if '*' in pattern and file_path.name.endswith(pattern.replace('*', '')):
                        self._log("debug", "File included by wildcard pattern",
                                file=str(file_path),
                                pattern=pattern,
                                reason="wildcard match")
                        return True
            self._log("debug", "File excluded by no include pattern match",
                     file=str(file_path))
            return False
            
        return True
        
    def _detect_language(self, file_path: Union[str, Path]) -> str:
        """Detect the programming language of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language identifier string
        """
        file_path = str(file_path)
        filename = Path(file_path).name.lower()
        
        # First check if we have a custom parser for this file
        custom_parser = get_custom_parser(file_path)
        if custom_parser:
            if isinstance(custom_parser, RequirementsParser):
                return "requirements"
            elif isinstance(custom_parser, EnvFileParser):
                return "env"
            elif isinstance(custom_parser, GitignoreParser):
                return "gitignore"
            elif isinstance(custom_parser, EditorConfigParser):
                return "editorconfig"
            elif isinstance(custom_parser, LockFileParser):
                return "lockfile"
        
        # If no custom parser, check special filenames
        if filename in SPECIAL_FILENAMES:
            return SPECIAL_FILENAMES[filename]
        
        # Use language service to detect language
        try:
            return self._language_service.get_language_for_file(file_path)
        except Exception as e:
            self._log("warning", f"Failed to detect language: {str(e)}", file_path=file_path)
            return "plaintext"
        
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

    def _should_exclude(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on default patterns.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the file should be excluded
        """
        # Check each path component against exclude patterns
        for part in file_path.parts:
            if part in DEFAULT_EXCLUDES:
                return True
                
            # Check wildcard patterns
            for pattern in DEFAULT_EXCLUDES:
                if '*' in pattern and Path(part).match(pattern):
                    return True
                    
        return False 

    def has_custom_parser(self, file_path: Union[str, Path]) -> bool:
        """Check if a file has a custom parser available.
        
        Args:
            file_path: Path to the file to check.
            
        Returns:
            True if a custom parser is available for this file type.
        """
        return get_custom_parser(str(file_path)) is not None 