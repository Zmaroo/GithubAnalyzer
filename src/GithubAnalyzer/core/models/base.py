"""Base models for parsing and analysis"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class ParseResult:
    """Result of parsing a file"""
    ast: Any  # Abstract syntax tree
    semantic: Dict[str, Any]  # Semantic information
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    success: bool = True
    tree_sitter_node: Optional[Any] = None  # Tree-sitter AST node if available 