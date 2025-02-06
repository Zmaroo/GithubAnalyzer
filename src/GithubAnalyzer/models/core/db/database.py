"""Database models for code storage and analysis."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from GithubAnalyzer.models.core.base_model import BaseModel
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class DatabaseConnection:
    """Base class for database connections."""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    def __post_init__(self):
        """Initialize and validate connection."""
        logger.debug("Initializing database connection", extra={
            'context': {
                'operation': 'initialization',
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'user': self.user,
                'has_password': bool(self.password)
            }
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert connection details to dictionary."""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }

@dataclass
class DatabaseModel(BaseModel):
    """Base class for database models."""
    _created_at: datetime = field(init=False, default_factory=datetime.now)
    _updated_at: Optional[datetime] = field(init=False, default=None)
    
    def __post_init__(self):
        """Initialize and validate model."""
        super().__post_init__()
        logger.debug("Initializing database model", extra={
            'context': {
                'operation': 'initialization',
                'model_type': self.__class__.__name__,
                'created_at': self._created_at,
                'updated_at': self._updated_at
            }
        })
    
    @property
    def created_at(self) -> datetime:
        """Get creation timestamp."""
        return self._created_at
    
    @property
    def updated_at(self) -> Optional[datetime]:
        """Get last update timestamp."""
        return self._updated_at
    
    def update(self):
        """Update the last update timestamp."""
        self._updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation."""
        return {
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat() if self._updated_at else None
        }

@dataclass
class CodeSnippet(DatabaseModel):
    """Model representing a code snippet in PostgreSQL.
    
    Attributes:
        id: Optional unique identifier
        repo_id: Repository identifier
        file_path: Path to the file containing the code
        code_text: The actual code text
        embedding: Vector embedding of the code
        language: Optional programming language
        ast_data: Optional AST data
        syntax_valid: Whether the code has valid syntax
        complexity_metrics: Optional code complexity metrics
        metadata: Optional metadata about the code snippet
    """
    id: Optional[int]
    repo_id: int
    file_path: str
    code_text: str
    embedding: List[float]
    language: Optional[str] = None
    ast_data: Optional[Dict[str, Any]] = None
    syntax_valid: bool = True
    complexity_metrics: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize and validate code snippet."""
        super().__post_init__()
        logger.debug("Initializing code snippet", extra={
            'context': {
                'operation': 'initialization',
                'repo_id': self.repo_id,
                'file_path': self.file_path,
                'language': self.language,
                'syntax_valid': self.syntax_valid,
                'has_ast': self.ast_data is not None,
                'has_metrics': self.complexity_metrics is not None
            }
        })
    
    def get_functions(self) -> List[Dict[str, Any]]:
        """Get functions from AST data."""
        if not self.ast_data or 'elements' not in self.ast_data:
            logger.debug("No AST data available for functions", extra={
                'context': {
                    'operation': 'get_functions',
                    'file_path': self.file_path
                }
            })
            return []
        functions = self.ast_data['elements'].get('function', [])
        logger.debug("Retrieved functions from AST", extra={
            'context': {
                'operation': 'get_functions',
                'file_path': self.file_path,
                'count': len(functions)
            }
        })
        return functions
        
    def get_classes(self) -> List[Dict[str, Any]]:
        """Get classes from AST data."""
        if not self.ast_data or 'elements' not in self.ast_data:
            logger.debug("No AST data available for classes", extra={
                'context': {
                    'operation': 'get_classes',
                    'file_path': self.file_path
                }
            })
            return []
        classes = self.ast_data['elements'].get('class', [])
        logger.debug("Retrieved classes from AST", extra={
            'context': {
                'operation': 'get_classes',
                'file_path': self.file_path,
                'count': len(classes)
            }
        })
        return classes

@dataclass
class Function(DatabaseModel):
    """Model representing a function node in Neo4j."""
    name: str
    file_path: str
    repo_id: int
    calls: List['Function'] = field(default_factory=list)
    language: Optional[str] = None
    ast_data: Optional[Dict[str, Any]] = None
    start_point: Optional[Dict[str, int]] = None
    end_point: Optional[Dict[str, int]] = None
    complexity: Optional[Dict[str, Any]] = None
    docstring: Optional[str] = None
    
    def __post_init__(self):
        """Initialize and validate function."""
        super().__post_init__()
        logger.debug("Initializing function", extra={
            'context': {
                'operation': 'initialization',
                'name': self.name,
                'file_path': self.file_path,
                'language': self.language,
                'call_count': len(self.calls),
                'has_ast': self.ast_data is not None,
                'has_complexity': self.complexity is not None,
                'has_docstring': self.docstring is not None
            }
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        data = {
            'name': self.name,
            'file_path': self.file_path,
            'repo_id': self.repo_id,
            'language': self.language,
            'ast_data': self.ast_data,
            'start_point': self.start_point,
            'end_point': self.end_point,
            'complexity': self.complexity,
            'docstring': self.docstring,
            'calls': [f.name for f in self.calls]
        }
        logger.debug("Converted function to dict", extra={
            'context': {
                'operation': 'to_dict',
                'name': self.name,
                'call_count': len(self.calls)
            }
        })
        return data

@dataclass
class Class(DatabaseModel):
    """Model representing a class node in Neo4j."""
    name: str
    file_path: str
    repo_id: int
    language: Optional[str] = None
    ast_data: Optional[Dict[str, Any]] = None
    methods: List[Function] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    
    def __post_init__(self):
        """Initialize and validate class."""
        super().__post_init__()
        logger.debug("Initializing class", extra={
            'context': {
                'operation': 'initialization',
                'name': self.name,
                'file_path': self.file_path,
                'language': self.language,
                'method_count': len(self.methods),
                'base_count': len(self.base_classes),
                'has_ast': self.ast_data is not None,
                'has_docstring': self.docstring is not None
            }
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        data = {
            'name': self.name,
            'file_path': self.file_path,
            'repo_id': self.repo_id,
            'language': self.language,
            'ast_data': self.ast_data,
            'methods': [m.name for m in self.methods],
            'base_classes': self.base_classes,
            'docstring': self.docstring
        }
        logger.debug("Converted class to dict", extra={
            'context': {
                'operation': 'to_dict',
                'name': self.name,
                'method_count': len(self.methods)
            }
        })
        return data

@dataclass
class File(DatabaseModel):
    """Model representing a file node in Neo4j."""
    path: str
    repo_id: int
    functions: List[Function] = field(default_factory=list)
    language: Optional[str] = None
    classes: List[Class] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    ast_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize and validate file."""
        super().__post_init__()
        logger.debug("Initializing file", extra={
            'context': {
                'operation': 'initialization',
                'path': self.path,
                'language': self.language,
                'function_count': len(self.functions),
                'class_count': len(self.classes),
                'import_count': len(self.imports),
                'has_ast': self.ast_data is not None
            }
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        data = {
            'path': self.path,
            'repo_id': self.repo_id,
            'language': self.language,
            'functions': [f.to_dict() for f in self.functions],
            'classes': [c.to_dict() for c in self.classes],
            'imports': self.imports,
            'ast_data': self.ast_data
        }
        logger.debug("Converted file to dict", extra={
            'context': {
                'operation': 'to_dict',
                'path': self.path,
                'function_count': len(self.functions),
                'class_count': len(self.classes)
            }
        })
        return data

@dataclass
class CodebaseQuery(DatabaseModel):
    """Model representing a codebase query result."""
    semantic_matches: List[CodeSnippet]
    structural_relationships: List[Dict[str, Any]]
    community_data: Optional[Dict[str, List[str]]] = None
    centrality_metrics: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        """Initialize and validate query result."""
        super().__post_init__()
        logger.debug("Initializing codebase query", extra={
            'context': {
                'operation': 'initialization',
                'match_count': len(self.semantic_matches),
                'relationship_count': len(self.structural_relationships),
                'has_community_data': self.community_data is not None,
                'has_centrality': self.centrality_metrics is not None
            }
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get query result summary."""
        summary = {
            'match_count': len(self.semantic_matches),
            'relationship_count': len(self.structural_relationships),
            'has_community_data': bool(self.community_data),
            'has_centrality_metrics': bool(self.centrality_metrics)
        }
        logger.debug("Generated query summary", extra={
            'context': {
                'operation': 'get_summary',
                'summary': summary
            }
        })
        return summary

@dataclass
class GraphAnalytics(DatabaseModel):
    """Model representing graph analytics results."""
    central_components: List[Dict[str, Any]]
    critical_paths: List[List[str]]
    communities: Dict[str, List[str]]
    similarity_scores: Dict[str, float]
    
    def __post_init__(self):
        """Initialize and validate analytics."""
        super().__post_init__()
        logger.debug("Initializing graph analytics", extra={
            'context': {
                'operation': 'initialization',
                'component_count': len(self.central_components),
                'path_count': len(self.critical_paths),
                'community_count': len(self.communities),
                'similarity_count': len(self.similarity_scores)
            }
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get analytics summary."""
        summary = {
            'component_count': len(self.central_components),
            'path_count': len(self.critical_paths),
            'community_count': len(self.communities),
            'similarity_count': len(self.similarity_scores)
        }
        logger.debug("Generated analytics summary", extra={
            'context': {
                'operation': 'get_summary',
                'summary': summary
            }
        })
        return summary

@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    host: str
    port: int
    database: str
    user: str
    password: str
    uri: Optional[str] = None
    username: Optional[str] = None
    
    def __post_init__(self):
        """Initialize and validate database configuration."""
        logger.debug("Initializing database configuration", extra={
            'context': {
                'operation': 'initialization',
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'user': self.user,
                'has_password': bool(self.password),
                'has_uri': bool(self.uri),
                'has_username': bool(self.username)
            }
        })
    
    def to_postgres_config(self) -> Dict[str, Any]:
        """Convert to PostgreSQL configuration dictionary."""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }
    
    def to_neo4j_config(self) -> Dict[str, str]:
        """Convert to Neo4j configuration dictionary."""
        if not self.uri or not self.username:
            raise ValueError("URI and username are required for Neo4j configuration")
        return {
            'uri': self.uri,
            'username': self.username,
            'password': self.password
        }
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create configuration from environment variables."""
        from GithubAnalyzer.services.core.database.db_config import (
            get_neo4j_config, get_postgres_config)
        
        pg_config = get_postgres_config()
        neo4j_config = get_neo4j_config()
        
        return cls(
            host=pg_config['host'],
            port=pg_config['port'],
            database=pg_config['database'],
            user=pg_config['user'],
            password=pg_config['password'],
            uri=neo4j_config['uri'],
            username=neo4j_config['username']
        ) 