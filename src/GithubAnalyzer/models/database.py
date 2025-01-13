"""Database related models"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

@dataclass
class DatabaseConfig:
    """Database configuration"""
    pg_conn_string: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    redis_host: str
    redis_port: int
    use_cache: bool = True

@dataclass
class DatabaseError(Exception):
    """Database error"""
    message: str
    code: Optional[int] = None

    def __str__(self) -> str:
        return f"DatabaseError({self.code}): {self.message}"

@dataclass
class RepositoryState:
    """Repository analysis state"""
    url: str
    status: str
    progress: float
    errors: List[str] = field(default_factory=list)
    last_update: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    current_operation: Optional[str] = None
    operation_started: Optional[datetime] = None
    operation_progress: float = 0.0

@dataclass
class RepositoryInfo:
    """Repository information"""
    name: str
    url: str
    local_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_analyzed: datetime = field(default_factory=datetime.now)
    frameworks: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    is_current: bool = False
    analysis_status: str = "pending"
    analysis_errors: List[str] = field(default_factory=list)

@dataclass
class GraphRelationship:
    """Graph relationship information"""
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    start_node: str = ""  # ID of the start node
    end_node: str = ""    # ID of the end node
    id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class GraphNode:
    """Graph node information"""
    id: str
    labels: List[str]
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class DatabaseConnection:
    """Database connection information"""
    pg_conn: Any = None
    neo4j_conn: Any = None
    redis_conn: Any = None
    is_connected: bool = False
    last_error: Optional[str] = None 