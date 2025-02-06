"""Core type definitions."""
from dataclasses import dataclass
from typing import Any, Dict, List, NewType, Set, Tuple, Union

from tree_sitter import Node

# Core type definitions
LanguageId = NewType('LanguageId', str)  # Unique identifier for a language
FileId = NewType('FileId', str)  # Unique identifier for a file
RepoId = NewType('RepoId', str)  # Unique identifier for a repository
NodeId = NewType('NodeId', str)  # Unique identifier for an AST node
QueryId = NewType('QueryId', str)  # Unique identifier for a query

# Type enums
LanguageType = str  # Type of programming language
FileType = str  # Type of file (source, config, etc.)
NodeType = str  # Type of AST node
QueryType = str  # Type of query (semantic, structural, etc.)

# Common type aliases
JsonDict = Dict[str, Any]  # Generic JSON-like dictionary
PathStr = str  # File system path string
ContentStr = str  # File content string
LineList = List[str]  # List of text lines

# Result types
Result = Dict[str, Any]  # Generic result dictionary
ErrorResult = Dict[str, Union[str, List[str]]]  # Error result with messages

# AST node types
NodeDict = Dict[str, Any]  # Dictionary representation of an AST node
NodeList = List[Node]  # List of tree-sitter nodes
NodeSet = Set[Node]  # Set of tree-sitter nodes
NodeMap = Dict[str, Node]  # Map of node names to nodes

# Tree-sitter types
@dataclass
class TreeSitterRange:
    """Represents a range in a tree-sitter tree."""
    start_point: Tuple[int, int]  # (row, column)
    end_point: Tuple[int, int]  # (row, column)
    start_byte: int
    end_byte: int

    def contains(self, other: 'TreeSitterRange') -> bool:
        """Check if this range contains another range."""
        return (self.start_byte <= other.start_byte and
                self.end_byte >= other.end_byte)
    
    def overlaps(self, other: 'TreeSitterRange') -> bool:
        """Check if this range overlaps with another range."""
        return not (self.end_byte < other.start_byte or
                   self.start_byte > other.end_byte) 