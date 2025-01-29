"""Database models for code storage and analysis."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Set

@dataclass
class CodeSnippet:
    """Model representing a code snippet in PostgreSQL."""
    id: Optional[int]
    repo_id: int
    file_path: str
    code_text: str
    embedding: List[float]
    created_at: datetime
    language: Optional[str] = None
    ast_data: Optional[Dict[str, Any]] = None
    syntax_valid: bool = True
    complexity_metrics: Optional[Dict[str, Any]] = None
    
    def get_functions(self) -> List[Dict[str, Any]]:
        """Get functions from AST data."""
        if not self.ast_data or 'elements' not in self.ast_data:
            return []
        return self.ast_data['elements'].get('function', [])
        
    def get_classes(self) -> List[Dict[str, Any]]:
        """Get classes from AST data."""
        if not self.ast_data or 'elements' not in self.ast_data:
            return []
        return self.ast_data['elements'].get('class', [])

@dataclass
class Function:
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
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

@dataclass
class Class:
    """Model representing a class node in Neo4j."""
    name: str
    file_path: str
    repo_id: int
    language: Optional[str] = None
    ast_data: Optional[Dict[str, Any]] = None
    methods: List[Function] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'file_path': self.file_path,
            'repo_id': self.repo_id,
            'language': self.language,
            'ast_data': self.ast_data,
            'methods': [m.name for m in self.methods],
            'base_classes': self.base_classes,
            'docstring': self.docstring
        }

@dataclass
class File:
    """Model representing a file node in Neo4j."""
    path: str
    repo_id: int
    functions: List[Function] = field(default_factory=list)
    language: Optional[str] = None
    classes: List[Class] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    ast_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'path': self.path,
            'repo_id': self.repo_id,
            'language': self.language,
            'functions': [f.to_dict() for f in self.functions],
            'classes': [c.to_dict() for c in self.classes],
            'imports': self.imports,
            'ast_data': self.ast_data
        }

@dataclass
class CodebaseQuery:
    """Model representing a codebase query result."""
    semantic_matches: List[CodeSnippet]
    structural_relationships: List[Dict[str, Any]]
    community_data: Optional[Dict[str, List[str]]] = None
    centrality_metrics: Optional[Dict[str, float]] = None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get query result summary."""
        return {
            'match_count': len(self.semantic_matches),
            'relationship_count': len(self.structural_relationships),
            'has_community_data': bool(self.community_data),
            'has_centrality_metrics': bool(self.centrality_metrics)
        }

@dataclass
class GraphAnalytics:
    """Model representing graph analytics results."""
    central_components: List[Dict[str, Any]]
    critical_paths: List[List[str]]
    communities: Dict[str, List[str]]
    similarity_scores: Dict[str, float]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get analytics summary."""
        return {
            'component_count': len(self.central_components),
            'path_count': len(self.critical_paths),
            'community_count': len(self.communities),
            'similarity_count': len(self.similarity_scores)
        } 