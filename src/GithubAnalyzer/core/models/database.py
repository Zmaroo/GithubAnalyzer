"""Database related models"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .graph import GraphNode, GraphEdge

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int
    username: str
    password: str
    database: str

@dataclass
class DatabaseError:
    """Database error"""
    message: str
    code: Optional[int] = None

@dataclass
class RepositoryState:
    """Repository analysis state"""
    url: str
    status: str
    progress: float
    errors: Optional[list] = None

@dataclass
class RepositoryInfo:
    """Repository information"""
    name: str
    url: str
    local_path: str
    metadata: Dict[str, Any] 