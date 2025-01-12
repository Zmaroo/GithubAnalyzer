from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .code import ModuleInfo, CodeRelationships
import time

@dataclass
class AnalysisResult:
    """Results from code analysis"""
    modules: List[ModuleInfo]
    relationships: CodeRelationships
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

@dataclass
class AnalysisContext:
    """Context for analysis operations"""
    repository: str
    current_file: Optional[str] = None
    cache_enabled: bool = True
    include_metrics: bool = True
    max_file_size: int = 1024 * 1024  # 1MB default

@dataclass
class AnalysisProgress:
    """Analysis progress tracking"""
    total_files: int = 0
    processed_files: int = 0
    current_file: Optional[str] = None
    stage: str = 'initializing'
    estimated_completion: Optional[float] = None

@dataclass
class AnalysisMetadata:
    """Metadata about analysis process"""
    tool_version: str
    timestamp: float = field(default_factory=lambda: time.time())
    duration: float = 0.0
    files_analyzed: int = 0
    total_lines: int = 0
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RepositoryMetrics:
    """Repository-wide metrics"""
    total_files: int = 0
    total_lines: int = 0
    code_to_comment_ratio: float = 0.0
    avg_complexity: float = 0.0
    test_coverage: float = 0.0
    documentation_coverage: float = 0.0
    maintainability_index: float = 0.0 