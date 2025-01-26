from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class CodeSnippet:
    """Model representing a code snippet in PostgreSQL."""
    id: Optional[int]
    repo_id: str
    file_path: str
    code_text: str
    embedding: List[float]
    created_at: datetime

@dataclass
class Function:
    """Model representing a function node in Neo4j."""
    name: str
    file_path: str
    calls: List['Function']
    repo_id: str

@dataclass
class File:
    """Model representing a file node in Neo4j."""
    path: str
    repo_id: str
    functions: List[Function]

@dataclass
class CodebaseQuery:
    """Model representing a codebase query result."""
    semantic_matches: List[CodeSnippet]
    structural_relationships: List[Dict[str, Any]] 