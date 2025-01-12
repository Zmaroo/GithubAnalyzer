from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Literal
import time

@dataclass
class DatabaseConfig:
    """Database configuration"""
    pg_conn_string: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    redis_host: str = 'localhost'
    redis_port: int = 6379
    use_cache: bool = True

@dataclass
class GraphQuery:
    """Neo4j graph query"""
    query: str
    params: Dict[str, Any] = field(default_factory=dict)
    result_type: Literal['node', 'relationship', 'path', 'value'] = 'node'
    limit: Optional[int] = None

@dataclass
class RepositoryState:
    """Repository analysis state"""
    url: str
    status: Literal['pending', 'analyzing', 'completed', 'failed']
    last_update: float = field(default_factory=time.time)
    progress: float = 0.0
    current_operation: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class RepositoryInfo:
    """Repository information"""
    name: str
    url: str
    local_path: str
    last_analyzed: Optional[str] = None
    is_current: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphNode:
    """Neo4j graph node"""
    id: str
    labels: List[str]
    properties: Dict[str, Any]

@dataclass
class GraphRelationship:
    """Neo4j graph relationship"""
    type: str
    start_node: GraphNode
    end_node: GraphNode
    properties: Dict[str, Any] = field(default_factory=dict) 