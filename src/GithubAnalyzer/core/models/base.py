from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class BaseModel:
    """Base class for all data models"""
    pass

@dataclass
class TreeSitterNode:
    """Tree-sitter AST node representation"""
    type: str
    text: str
    start_point: tuple
    end_point: tuple
    children: List['TreeSitterNode']

@dataclass
class ParseResult:
    """Result from any parser"""
    ast: Optional[Any]
    semantic: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    success: bool = True
    tree_sitter_node: Optional[TreeSitterNode] = None 