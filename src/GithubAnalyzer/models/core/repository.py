"""Repository information models"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class RepositoryInfo:
    """Information about a Git repository"""
    name: str
    url: str
    local_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    size: Optional[int] = None
    language: Optional[str] = None
    branch: str = "main"
    commit_hash: Optional[str] = None

@dataclass
class RepositoryState:
    """State of repository analysis"""
    url: str
    status: str  # analyzing, completed, failed
    progress: float = 0.0
    current_operation: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict) 