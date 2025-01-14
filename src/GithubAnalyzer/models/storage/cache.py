"""Analysis cache models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..base import BaseModel


@dataclass
class AnalysisCache(BaseModel):
    """Cache for analysis results."""

    key: str
    value: Any
    expiry: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisSession(BaseModel):
    """Analysis session information."""

    id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeSnippet(BaseModel):
    """Code snippet with metadata."""

    content: str
    language: str
    file_path: str
    start_line: int
    end_line: int
    metadata: Dict[str, Any] = field(default_factory=dict)
