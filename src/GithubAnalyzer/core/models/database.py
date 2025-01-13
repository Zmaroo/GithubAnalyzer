"""Database models and configuration"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    pg_conn_string: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    redis_host: str
    redis_port: int
    use_cache: bool = True

@dataclass
class DatabaseError:
    """Database operation error"""
    message: str
    code: Optional[str] = None
    details: Optional[dict] = None
    recoverable: bool = False
    
    def __str__(self) -> str:
        return f"Database error: {self.message} (code={self.code})" 

@dataclass
class RepositoryInfo:
    """Repository information"""
    name: str
    url: str
    local_path: str
    last_analyzed: Optional[str] = None
    is_current: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class RepositoryState:
    """Repository analysis state"""
    url: str
    status: str
    progress: float = 0.0
    current_operation: Optional[str] = None
    last_update: Optional[float] = None
    errors: List[str] = field(default_factory=list) 