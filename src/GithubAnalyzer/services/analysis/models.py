"""Analysis models."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CodeAnalysis:
    """Result of code analysis."""

    file_path: str
    language: str
    ast: Optional[Dict] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """Result of repository analysis."""

    repository_name: str
    language: str
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
