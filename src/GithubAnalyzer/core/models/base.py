"""Base models for parsing and analysis"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple

@dataclass
class TreeSitterNode:
    """Tree-sitter AST node representation"""
    type: str
    text: str
    start_point: Tuple[int, int]  # (line, column)
    end_point: Tuple[int, int]    # (line, column)
    children: List['TreeSitterNode'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': self.type,
            'text': self.text,
            'start_point': self.start_point,
            'end_point': self.end_point,
            'children': [child.to_dict() for child in self.children]
        }

@dataclass
class ParseResult:
    """Result of parsing a file"""
    ast: Optional[TreeSitterNode]  # Converted AST node
    semantic: Dict[str, Any]  # Semantic information extracted from AST
    errors: List[str] = field(default_factory=list)  # Error messages if parsing failed
    warnings: List[str] = field(default_factory=list)  # Warning messages for potential issues
    success: bool = True  # Whether parsing was successful
    raw_ast: Optional[Any] = None  # Raw AST from parser before conversion
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format expected by tests"""
        return {
            'success': self.success,
            'ast': self.ast.to_dict() if self.ast else None,
            'semantic': self.semantic,
            'errors': self.errors,
            'warnings': self.warnings,
            'tree_sitter_node': self.ast.to_dict() if self.ast else None  # For backward compatibility
        } 