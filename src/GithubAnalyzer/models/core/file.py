"""File-related data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Union

if TYPE_CHECKING:
    from GithubAnalyzer.models.analysis.language import LanguageDetectionResult

# Commenting out the top-level import that causes circular dependency
# from GithubAnalyzer.models.analysis.language import LanguageDetectionResult

from GithubAnalyzer.models.core.base_model import BaseModel
from GithubAnalyzer.models.core.language import (EXTENSION_TO_LANGUAGE,
                                                 LANGUAGE_FEATURES,
                                                 SPECIAL_FILENAMES,
                                                 LanguageFeatures,
                                                 LanguageInfo)
from GithubAnalyzer.models.core.parsers import get_custom_parser
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class FileInfo(BaseModel):
    """Basic file information."""
    path: Path
    language: str = 'unknown'
    repo_id: int = 0
    metadata: Optional[Dict[str, Any]] = None
    is_supported: bool = True
    features: Optional[Any] = None
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize and validate file info."""
        super().__post_init__()
        
        # Handle special cases first
        filename = self.path.name.lower()
        if filename == "license" or filename == "license.txt":
            self.language = "plaintext"
            self.is_supported = False
            logger.debug("File identified as license", extra={
                'context': {
                    'operation': 'language_detection',
                    'path': str(self.path),
                    'language': self.language,
                    'is_supported': self.is_supported
                }
            })
            return
            
        # Get language from detection
        try:
            # First try by filename
            filename = str(self.path).lower()
            for special_name, lang in SPECIAL_FILENAMES.items():
                if filename.endswith(special_name):
                    self.language = lang
                    self.features = LANGUAGE_FEATURES.get(lang)
                    self.is_supported = True
                    return
            
            # Then try by extension
            extension = self.path.suffix.lower()[1:] if self.path.suffix else ''
            if extension in EXTENSION_TO_LANGUAGE:
                self.language = EXTENSION_TO_LANGUAGE[extension]
                self.features = LANGUAGE_FEATURES.get(self.language)
                self.is_supported = True
                return
                
            # Default to plaintext if no match
            self.language = 'plaintext'
            self.is_supported = False
            
            logger.debug("Language detected", extra={
                'context': {
                    'operation': 'language_detection',
                    'path': str(self.path),
                    'language': self.language,
                    'is_supported': self.is_supported,
                    'has_features': bool(self.features),
                    'error_count': len(self.errors)
                }
            })
                
        except Exception as e:
            logger.error("Error detecting language for file", extra={
                'context': {
                    'operation': 'language_detection',
                    'path': str(self.path),
                    'error': str(e)
                }
            })
            self.language = 'plaintext'
            self.is_supported = False

def _detect_language(file_path: str) -> "LanguageDetectionResult":
    """Detect language from file path."""
    # First try by filename
    filename = file_path.lower()
    for special_name, language in SPECIAL_FILENAMES.items():
        if filename.endswith(special_name):
            return LanguageDetectionResult(
                file_path=file_path,
                language=language,
                confidence=1.0,
                is_supported=True,
                features=LANGUAGE_FEATURES.get(language)
            )
    
    # Then try by extension
    extension = file_path.split('.')[-1].lower() if '.' in file_path else ''
    if extension in EXTENSION_TO_LANGUAGE:
        language = EXTENSION_TO_LANGUAGE[extension]
        return LanguageDetectionResult(
            file_path=file_path,
            language=language,
            confidence=1.0,
            is_supported=True,
            features=LANGUAGE_FEATURES.get(language)
        )
    
    # Default to plaintext if no match
    return LanguageDetectionResult(
        file_path=file_path,
        language='plaintext',
        confidence=0.5,
        is_supported=False
    )

# Standard exclude sets
GIT_EXCLUDES: Set[str] = {
    '.git',
    '.gitignore',
    '.gitattributes',
    '.gitmodules',
    '.github',
    '.gitkeep'
}

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
    '.pytest_cache'
}

EDITOR_EXCLUDES: Set[str] = {
    '.idea',
    '.vscode',
    '*.swp',
    '*.swo',
    '*~',
    '.DS_Store'
}

DEFAULT_EXCLUDES: Set[str] = GIT_EXCLUDES | BUILD_EXCLUDES | EDITOR_EXCLUDES

@dataclass
class FileModel(BaseModel):
    """Model for file operations."""
    path: Path
    content: Optional[str] = None
    language: Optional[str] = None
    ast: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize and validate file model."""
        super().__post_init__()
        if not self.language and self.path:
            result = _detect_language(str(self.path))
            self.language = result.language
        
        logger.debug("Initializing file model", extra={
            'context': {
                'operation': 'initialization',
                'path': str(self.path),
                'language': self.language,
                'has_content': bool(self.content),
                'has_ast': bool(self.ast)
            }
        })
    
    @classmethod
    def from_path(cls, path: Path) -> 'FileModel':
        """Create file model from path."""
        return cls(path=path)
    
    @classmethod
    def from_content(cls, content: str, path: Optional[Path] = None) -> 'FileModel':
        """Create file model from content."""
        return cls(path=path or Path('unknown'), content=content)

@dataclass
class FilePattern:
    """File pattern for matching files."""
    pattern: str
    is_regex: bool = False
    case_sensitive: bool = False
    
    def __post_init__(self):
        """Initialize pattern."""
        logger.debug("Initializing file pattern", extra={
            'context': {
                'operation': 'initialization',
                'pattern': self.pattern,
                'is_regex': self.is_regex,
                'case_sensitive': self.case_sensitive
            }
        })

@dataclass
class FileFilterConfig:
    """Configuration for filtering files."""
    include_languages: Optional[List[str]] = None
    exclude_languages: Optional[List[str]] = None
    include_paths: Optional[List[str]] = None
    exclude_paths: Optional[List[str]] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    use_default_excludes: bool = True
    custom_excludes: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Initialize filter config."""
        logger.debug("Initializing file filter config", extra={
            'context': {
                'operation': 'initialization',
                'include_languages': self.include_languages,
                'exclude_languages': self.exclude_languages,
                'include_paths': self.include_paths,
                'exclude_paths': self.exclude_paths,
                'min_size': self.min_size,
                'max_size': self.max_size,
                'use_default_excludes': self.use_default_excludes,
                'custom_excludes_count': len(self.custom_excludes)
            }
        })
        
        # Initialize exclude paths with defaults if needed
        if self.use_default_excludes:
            if self.exclude_paths is None:
                self.exclude_paths = []
            self.exclude_paths.extend(DEFAULT_EXCLUDES)
            
        # Add custom excludes
        if self.custom_excludes:
            if self.exclude_paths is None:
                self.exclude_paths = []
            self.exclude_paths.extend(self.custom_excludes)

    def matches(self, file_info: FileInfo) -> bool:
        """Check if a file matches the filter configuration."""
        try:
            # Check language filters
            if self.include_languages and file_info.language not in self.include_languages:
                logger.debug("File excluded by language filter", extra={
                    'context': {
                        'operation': 'filter_match',
                        'path': str(file_info.path),
                        'language': file_info.language,
                        'filter': 'include_languages'
                    }
                })
                return False
                
            if self.exclude_languages and file_info.language in self.exclude_languages:
                logger.debug("File excluded by language filter", extra={
                    'context': {
                        'operation': 'filter_match',
                        'path': str(file_info.path),
                        'language': file_info.language,
                        'filter': 'exclude_languages'
                    }
                })
                return False
                
            # Check path filters
            if self.include_paths:
                matches = False
                for pattern in self.include_paths:
                    # Check if pattern is a full path pattern (contains '/')
                    if '/' in pattern:
                        if file_info.path.match(pattern):
                            matches = True
                            break
                    else:
                        # For simple patterns, only match against the file name
                        if file_info.path.name == pattern:
                            matches = True
                            break
                        # For wildcard patterns, match against the file name
                        if '*' in pattern and file_info.path.name.endswith(pattern.replace('*', '')):
                            matches = True
                            break
                if not matches:
                    logger.debug("File excluded by path filter", extra={
                        'context': {
                            'operation': 'filter_match',
                            'path': str(file_info.path),
                            'filter': 'include_paths'
                        }
                    })
                    return False
                    
            if self.exclude_paths:
                for pattern in self.exclude_paths:
                    # Check if pattern is a full path pattern (contains '/')
                    if '/' in pattern:
                        if file_info.path.match(pattern):
                            logger.debug("File excluded by path filter", extra={
                                'context': {
                                    'operation': 'filter_match',
                                    'path': str(file_info.path),
                                    'filter': 'exclude_paths',
                                    'pattern': pattern
                                }
                            })
                            return False
                    else:
                        # For simple patterns, only match against the file name
                        if file_info.path.name == pattern or file_info.path.name.startswith('.'):
                            logger.debug("File excluded by path filter", extra={
                                'context': {
                                    'operation': 'filter_match',
                                    'path': str(file_info.path),
                                    'filter': 'exclude_paths',
                                    'pattern': pattern
                                }
                            })
                            return False
                        # For wildcard patterns, match against the file name
                        if '*' in pattern and file_info.path.name.endswith(pattern.replace('*', '')):
                            logger.debug("File excluded by path filter", extra={
                                'context': {
                                    'operation': 'filter_match',
                                    'path': str(file_info.path),
                                    'filter': 'exclude_paths',
                                    'pattern': pattern
                                }
                            })
                            return False
                            
            logger.debug("File passed all filters", extra={
                'context': {
                    'operation': 'filter_match',
                    'path': str(file_info.path),
                    'result': True
                }
            })
            return True
            
        except Exception as e:
            logger.error("Error matching file filter", extra={
                'context': {
                    'operation': 'filter_match',
                    'path': str(file_info.path),
                    'error': str(e)
                }
            })
            return False 