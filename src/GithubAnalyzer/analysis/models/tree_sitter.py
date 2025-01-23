"""Tree-sitter models."""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from tree_sitter import Node, Tree

@dataclass
class TreeSitterNode:
    """Lightweight wrapper for tree-sitter Node with convenient properties."""
    node: Node
    metadata: Dict[str, Any] = None

    @property
    def type(self) -> str:
        """Get node type."""
        return self.node.type

    @property
    def text(self) -> str:
        """Get node text."""
        return self.node.text.decode('utf-8') if self.node.text else ""

    @property
    def start_point(self) -> tuple[int, int]:
        """Get start position (line, column)."""
        return self.node.start_point

    @property
    def end_point(self) -> tuple[int, int]:
        """Get end position (line, column)."""
        return self.node.end_point

    @property
    def children(self) -> List[Node]:
        """Get child nodes."""
        return self.node.children

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary."""
        return {
            'type': self.type,
            'text': self.text,
            'start_point': self.start_point,
            'end_point': self.end_point,
            'metadata': self.metadata or {}
        }

@dataclass
class QueryMatch:
    """Represents a query match result."""
    pattern_index: int
    captures: List[Tuple[str, Node]]
    node: Node

@dataclass
class TreeSitterError:
    """Tree-sitter specific error."""
    node: Optional[Node] = None
    message: str = ""
    line: int = 0
    column: int = 0
    context: str = ""

    @classmethod
    def from_node(cls, node: Node, source_lines: List[bytes]) -> 'TreeSitterError':
        """Create error from node."""
        line = node.start_point[0]
        column = node.start_point[1]
        context = source_lines[line].decode('utf-8') if line < len(source_lines) else ""
        return cls(
            node=node,
            message=f"Error at line {line + 1}, column {column + 1}",
            line=line,
            column=column,
            context=context
        )

class TreeSitterQueryError(TreeSitterError):
    """Error during tree-sitter query execution."""
    pass

@dataclass
class TreeSitterResult:
    """Result of tree-sitter parsing with analysis capabilities."""

    tree: Optional[Tree] = None
    recovery_attempts: int = 0
    text: Optional[str] = None

    def __init__(
        self,
        tree: Optional[Tree] = None,
        language: Optional[str] = None,
        is_valid: bool = True,
        errors: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        recovery_attempts: int = 0,
        text: Optional[str] = None
    ):
        """Initialize TreeSitterResult.
        
        Args:
            tree: Tree-sitter parse tree
            language: Language identifier
            is_valid: Whether parsing was successful
            errors: Any errors encountered during parsing
            metadata: Additional metadata
            recovery_attempts: Number of recovery attempts made
            text: Original text that was parsed
        """
        self.tree = tree
        self.recovery_attempts = recovery_attempts
        self.text = text

    def _calculate_node_count(self, tree: Optional[Tree]) -> int:
        """Calculate node count only when needed."""
        if not tree or not tree.root_node:
            return 0
            
        def count(node: Node) -> int:
            return 1 + sum(count(child) for child in node.children)
            
        return count(tree.root_node)

    @property
    def root(self) -> Optional[Node]:
        """Get the root node of the tree."""
        return self.tree.root_node if self.tree else None

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        base_dict = super().get_analysis_summary()
        return {
            **base_dict,
            'language': self.language,
            'errors': self.errors,
            'is_valid': self.is_valid,
            'metadata': self.metadata,
            'recovery_attempts': self.recovery_attempts,
            'has_tree': self.tree is not None,
            'text_length': len(self.text) if self.text else 0
        } 