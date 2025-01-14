"""Repository model definitions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class RepositoryInfo:
    """Information about a repository."""

    name: str
    url: str
    owner: str
    default_branch: str = "main"
    description: Optional[str] = None
    license: Optional[str] = None
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    languages: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    contributors: List[Dict[str, Any]] = field(default_factory=list)
    last_commit: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
