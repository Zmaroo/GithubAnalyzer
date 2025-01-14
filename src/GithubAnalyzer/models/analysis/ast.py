"""Abstract Syntax Tree (AST) models."""

from dataclasses import dataclass
from typing import Any, Dict, List

from ..core.base import BaseModel


@dataclass
class ParseResult(BaseModel):
    """Result of parsing a file or content."""

    def __init__(
        self,
        ast,
        language: str,
        is_valid: bool,
        line_count: int,
        node_count: int,
        errors: List[str],
        metadata: Dict[str, Any],
    ) -> None:
        """Initialize parse result.

        Args:
            ast: The abstract syntax tree
            language: Language identifier
            is_valid: Whether the parse was successful
            line_count: Number of lines parsed
            node_count: Number of AST nodes
            errors: List of error messages
            metadata: Additional metadata
        """
        self.ast = ast
        self.language = language
        self.is_valid = is_valid
        self.line_count = line_count
        self.node_count = node_count
        self.errors = errors
        self.metadata = metadata

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
