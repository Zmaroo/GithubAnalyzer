"""Analysis results models."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from ...core.models.base import BaseModel


@dataclass
class AnalysisResult(BaseModel):
    """Result of code analysis."""
    
    file_path: str
    language: str
    metrics: Dict[str, Any]
    findings: List[Dict[str, Any]]
    metadata: Dict[str, Any]
