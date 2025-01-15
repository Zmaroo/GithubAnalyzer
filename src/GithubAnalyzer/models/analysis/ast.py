"""AST analysis models."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from tree_sitter import Tree

from ..core.base import BaseModel


@dataclass
class ParseResult(BaseModel):
    """Result of parsing source code."""
    
    ast: Optional[Tree]  # Tree-sitter AST
    language: str        # Programming language identifier
    is_valid: bool      # Whether parsing succeeded
    line_count: int     # Number of lines in source
    node_count: int     # Number of AST nodes
    errors: List[str]   # List of parsing errors
    metadata: Dict[str, Any]  # Additional parsing metadata
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access for compatibility."""
        if key == "syntax_valid":
            return self.is_valid
        if hasattr(self, key):
            return getattr(self, key)
        if key in self.metadata:
            return self.metadata[key]
        raise KeyError(f"No such attribute or metadata key: {key}")
