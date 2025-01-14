"""Code metrics models."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..base import BaseModel


@dataclass
class CodeMetrics(BaseModel):
    """Code metrics information."""

    lines_of_code: int = 0
    comment_lines: int = 0
    docstring_lines: int = 0
    cyclomatic_complexity: float = 0.0
    maintainability_index: float = 0.0
    cognitive_complexity: float = 0.0
    test_coverage: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    function_count: int = 0
    class_count: int = 0
    method_count: int = 0
    attribute_count: int = 0
    test_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
