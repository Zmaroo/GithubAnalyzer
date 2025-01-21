"""Tree-sitter models and exceptions."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.GithubAnalyzer.core.models.errors import ParserError
from src.GithubAnalyzer.core.models.ast import ParseResult, Position, Range

@dataclass
class Position:
    """Source code position."""
    line: int
    column: int
    offset: int = 0  # Make offset optional with default value

@dataclass
class TreeSitterError(ParserError):
    """Tree-sitter specific parsing error."""
    message: str
    node_type: str
    position: Position
    
    def __init__(self, message: str, node_type: str, position: Position):
        """Initialize tree-sitter error.
        
        Args:
            message: Error message
            node_type: Type of node where error occurred
            position: Position in source code
        """
        super().__init__(message)
        self.message = message
        self.node_type = node_type
        self.position = position
        
    def format_message(self) -> str:
        """Format error message with position information.
        
        Returns:
            Formatted error message string
        """
        return f"{self.message} at line {self.position.line + 1}, column {self.position.column + 1}"
    
    @classmethod
    def from_node(cls, node: Any, lines: List[str]) -> 'TreeSitterError':
        """Create error from tree-sitter node."""
        error_msg = f"Error at node {node.type}"
        return cls(
            message=error_msg,  # Use keyword arg to match __init__ signature
            node_type=node.type,
            position=Position(
                line=node.start_point[0],
                column=node.start_point[1]
            )
        )

@dataclass
class TreeSitterQueryError(TreeSitterError):
    """Error raised during tree-sitter query execution."""
    query: str
    
    def __init__(self, message: str, query: str, node_type: str = "query", position: Optional[Position] = None):
        super().__init__(message=message, node_type=node_type, position=position or Position(0, 0))
        self.query = query

@dataclass
class TreeSitterResult(ParseResult):
    """Result from tree-sitter parsing."""
    tree: Any  # tree-sitter Tree object
    errors: List[TreeSitterError]
    node_count: int
    recovery_attempts: int = 0 