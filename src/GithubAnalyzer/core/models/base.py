"""Base models for parsing and analysis"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

@dataclass
class TreeSitterNode:
    """Tree-sitter AST node representation"""
    type: str
    text: str
    start_point: Tuple[int, int]  # (line, column)
    end_point: Tuple[int, int]    # (line, column)
    children: List['TreeSitterNode'] = field(default_factory=list)

@dataclass
class ParseResult:
    """Result of parsing a file"""
    ast: Any  # Abstract syntax tree
    semantic: Dict[str, Any]  # Semantic information
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    success: bool = True
    tree_sitter_node: Optional[TreeSitterNode] = None  # Tree-sitter AST node if available 