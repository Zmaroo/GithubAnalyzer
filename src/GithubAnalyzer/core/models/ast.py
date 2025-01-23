"""AST models for tree-sitter parsing."""

from dataclasses import dataclass
from typing import Optional, Any
from tree_sitter import Tree

@dataclass
class ParseResult:
    """Wrapper for tree-sitter parse results."""
    tree: Optional[Tree]  # The tree-sitter parse tree, None for non-code files
    language: str  # Language identifier or file type (e.g. 'python', 'yaml', 'markdown')
    content: str  # Raw file content
    is_code: bool = True  # Whether this is a code file parsed by tree-sitter 