"""Analysis result models."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..core.base import BaseModel
from ..core.errors import AnalysisError


@dataclass
class ImportInfo(BaseModel):
    """Information about an import statement."""

    name: str
    alias: Optional[str] = None
    is_from_import: bool = False
    imported_names: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class FunctionInfo(BaseModel):
    """Information about a function."""

    name: str
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    is_async: bool = False
    line_number: int = 0
    complexity: float = 0.0


@dataclass
class ClassInfo(BaseModel):
    """Information about a class."""

    name: str
    docstring: Optional[str] = None
    base_classes: List[str] = field(default_factory=list)
    methods: List[FunctionInfo] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class CodeMetrics(BaseModel):
    """Basic code metrics."""

    lines_of_code: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    complexity: float = 0.0


@dataclass
class CodeDependency(BaseModel):
    """Code dependency information."""

    source: str
    target: str
    type: str = "import"


@dataclass
class CodeAnalysis(BaseModel):
    """Code analysis results."""

    # Core information
    file_path: str
    language: str

    # Code structure
    imports: List[ImportInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)

    # Analysis results
    metrics: CodeMetrics = field(default_factory=CodeMetrics)
    dependencies: List[CodeDependency] = field(default_factory=list)

    # Issues and metadata
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

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

    # Analysis metadata
    timestamp: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
