"""Analysis result models."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..core.base import BaseModel
from ..core.errors import AnalysisError
from .module import Module
from .code import ClassInfo, FunctionInfo, ImportInfo
from .metrics import CodeMetrics
from .relationships import CodeDependency, CodeRelationship


@dataclass
class CodeAnalysis(BaseModel):
    """Code analysis results."""

    # Core information
    module: Module
    file_path: str
    language: str

    # Code structure
    imports: List[ImportInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)

    # Analysis results
    metrics: CodeMetrics = field(default_factory=CodeMetrics)
    relationships: List[CodeRelationship] = field(default_factory=list)
    dependencies: List[CodeDependency] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)

    # Issues and metadata
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    # Raw data
    ast: Optional[Dict] = None


@dataclass
class AnalysisResult(BaseModel):
    """Analysis result container."""

    # Project information
    repository_name: str
    language: str
    analyses: List[CodeAnalysis]

    # Overall metrics
    files_analyzed: int = 0
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    complexity: float = 0.0
    maintainability: float = 0.0

    # Analysis metadata
    timestamp: float = 0.0
    summary: Dict[str, str] = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
