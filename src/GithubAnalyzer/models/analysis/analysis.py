"""Analysis models and error definitions."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..core.module import Module


class AnalysisError(Exception):
    """Error raised during analysis operations."""


@dataclass
class CodeAnalysis:
    """Code analysis results."""

    module: Module
    file_path: str
    language: str
    metrics: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    ast: Optional[Dict] = None


@dataclass
class AnalysisResult:
    """Analysis result container."""

    repository_name: str
    language: str
    analyses: List[CodeAnalysis]
    summary: Dict[str, str]
    timestamp: float
    files_analyzed: int = 0
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    complexity: float = 0.0
    maintainability: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
