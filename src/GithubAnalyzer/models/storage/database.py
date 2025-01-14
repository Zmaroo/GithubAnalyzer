"""Database models and connection management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    pg_conn_string: str = "postgresql://localhost:5432/github_analyzer"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    redis_host: str = "localhost"
    redis_port: int = 6379
    max_connections: int = 10
    timeout: int = 30
    ssl_enabled: bool = False
    retry_attempts: int = 3


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
    end_node: str = ""  # ID of the end node
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
    """Database connection manager."""

    config: DatabaseConfig
    connection_type: str
    is_connected: bool = False
    last_error: Optional[str] = None

    def __enter__(self):
        """Enter context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.close()

    def connect(self) -> bool:
        """Establish database connection.

        Returns:
            True if connection successful, False otherwise.
        """
        try:
            # Connection logic here
            self.is_connected = True
            return True
        except Exception as e:
            self.last_error = str(e)
            self.is_connected = False
            return False

    def close(self) -> None:
        """Close database connection."""
        if self.is_connected:
            # Cleanup logic here
            self.is_connected = False
