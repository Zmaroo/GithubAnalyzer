"""Analysis statistics models."""

from dataclasses import dataclass, field
from typing import Dict, List

from ..base import BaseModel


@dataclass
class AnalysisStats(BaseModel):
    """Statistics from code analysis."""

    files_analyzed: int = 0
    files_with_errors: int = 0
    files_with_docs: int = 0
    failed_files: int = 0
    total_lines: int = 0
    code_lines: int = 0
    doc_lines: int = 0
    comment_lines: int = 0
    complexity_scores: Dict[str, float] = field(default_factory=dict)
    error_types: Dict[str, int] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
