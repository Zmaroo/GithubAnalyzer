"""Query response models."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class QueryResponse:
    """Response from a database query."""

    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_successful: bool = True
    total_results: int = 0
    execution_time: float = 0.0
    query_type: Optional[str] = None
