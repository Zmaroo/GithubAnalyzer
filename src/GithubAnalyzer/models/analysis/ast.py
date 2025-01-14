"""AST models for code analysis."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from ..core.base import BaseModel


@dataclass
class ParseResult(BaseModel):
    """Result of parsing a file or code snippet."""

    ast: Optional[Any]  # Tree-sitter AST or other parser-specific AST
    language: str  # Language identifier
    is_valid: bool  # Whether the parse was successful
    line_count: int  # Number of lines in the source
    node_count: int  # Number of AST nodes
    errors: List[str]  # List of parsing errors
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to attributes."""
        if key == "syntax_valid":
            return self.is_valid
        if hasattr(self, key):
            return getattr(self, key)
        if key in self.metadata:
            return self.metadata[key]
        raise KeyError(f"No such attribute or metadata key: {key}")

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return hasattr(self, key) or key in self.metadata
