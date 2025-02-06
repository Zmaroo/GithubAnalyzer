"""Repository-related models."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from GithubAnalyzer.models.core.base_model import BaseModel
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ProcessingStats(BaseModel):
    """Statistics about repository processing."""
    total_files: int = 0
    processed_files: int = 0
    error_files: int = 0
    skipped_files: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    language_counts: Dict[str, int] = field(default_factory=dict)
    error_messages: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize processing stats."""
        super().__post_init__()
        if not self.start_time:
            self.start_time = datetime.now()
        self._log("debug", "Processing stats initialized")

    def increment_processed(self):
        """Increment processed files count."""
        self.processed_files += 1
        self._log("debug", "Incremented processed files",
                processed=self.processed_files,
                total=self.total_files)

    def increment_errors(self, error_message: str):
        """Increment error files count.
        
        Args:
            error_message: Error message to log
        """
        self.error_files += 1
        self.error_messages.append(error_message)
        self._log("error", "Processing error occurred",
                error_count=self.error_files,
                error=error_message)

    def increment_skipped(self):
        """Increment skipped files count."""
        self.skipped_files += 1
        self._log("debug", "Skipped file",
                skipped=self.skipped_files,
                total=self.total_files)

    def add_language(self, language: str):
        """Increment count for a language.
        
        Args:
            language: Language identifier
        """
        self.language_counts[language] = self.language_counts.get(language, 0) + 1
        self._log("debug", "Added language count",
                language=language,
                count=self.language_counts[language])

    def complete(self):
        """Mark processing as complete."""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        self._log("info", "Processing completed",
                duration_seconds=duration,
                processed=self.processed_files,
                errors=self.error_files,
                skipped=self.skipped_files)

@dataclass
class ProcessingResult(BaseModel):
    """Result of processing a repository."""
    repo_id: str
    stats: ProcessingStats
    files: List[Path] = field(default_factory=list)
    languages: Set[str] = field(default_factory=set)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize processing result."""
        super().__post_init__()
        self._log("debug", "Processing result initialized",
                repo_id=self.repo_id)

    def add_file(self, file_path: Path, language: str):
        """Add a processed file.
        
        Args:
            file_path: Path to the file
            language: Language of the file
        """
        self.files.append(file_path)
        self.languages.add(language)
        self.stats.add_language(language)
        self._log("debug", "Added processed file",
                file=str(file_path),
                language=language)

    def add_error(self, error: str):
        """Add an error message.
        
        Args:
            error: Error message
        """
        self.errors.append(error)
        self.stats.increment_errors(error)
        self._log("error", "Added processing error",
                error=error)

    def update_metadata(self, key: str, value: Any):
        """Update metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self._log("debug", "Updated metadata",
                key=key,
                value=value)

@dataclass
class RepositoryInfo(BaseModel):
    """Information about a repository."""
    repo_id: str
    url: str
    name: Optional[str] = None
    description: Optional[str] = None
    default_branch: str = "main"
    languages: Set[str] = field(default_factory=set)
    file_count: int = 0
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize repository info."""
        super().__post_init__()
        if not self.name and self.url:
            self.name = self.url.split("/")[-1]
        if not self.last_updated:
            self.last_updated = datetime.now()
        self._log("debug", "Repository info initialized",
                repo_id=self.repo_id,
                name=self.name)

    def update_stats(self, stats: ProcessingStats):
        """Update repository stats.
        
        Args:
            stats: Processing stats to update from
        """
        self.file_count = stats.total_files
        self.languages.update(stats.language_counts.keys())
        self.last_updated = datetime.now()
        self._log("debug", "Updated repository stats",
                file_count=self.file_count,
                language_count=len(self.languages)) 