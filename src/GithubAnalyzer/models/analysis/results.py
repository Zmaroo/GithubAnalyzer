"""Analysis results models."""

from dataclasses import dataclass
from typing import Any, Dict, List

from ..core.base import BaseModel


@dataclass
class AnalysisResult(BaseModel):
    """Result of code analysis."""
    
    file_path: str
    language: str
    metrics: Dict[str, Any]
    findings: List[Dict[str, Any]]
    metadata: Dict[str, Any]
