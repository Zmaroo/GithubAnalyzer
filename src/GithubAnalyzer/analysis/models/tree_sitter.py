"""Tree-sitter specific data models."""

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from tree_sitter import Node, Tree, TreeCursor, Language, Parser, Point, Range, Query


class TreeSitterNodeType(Enum):
    """Common node types across languages."""
    MODULE = "module"
    PROGRAM = "program"
    FUNCTION = "function_definition"
    CLASS = "class_definition"
    METHOD = "method_definition"
    VARIABLE = "variable_declaration"
    IMPORT = "import_statement"
    COMMENT = "comment"
    ERROR = "ERROR"


class TreeSitterLogType(Enum):
    """Types of tree-sitter log messages."""
    PARSE = auto()
    LEX = auto()
    DEBUG = auto()


@dataclass
class TreeSitterConfig:
    """Configuration for tree-sitter parser."""
    languages: List[str]
    debug: bool = False
    print_tree: bool = False
    timeout_ms: int = 5000
    max_buffer_size: int = 1024 * 1024  # 1MB
    cache_size: int = 100  # Number of ASTs to cache
    log_level: TreeSitterLogType = TreeSitterLogType.PARSE


@dataclass
class TreeSitterRange:
    """Represents a range in the source code."""
    start_point: Point
    end_point: Point
    start_byte: int
    end_byte: int

    @classmethod
    def from_tree_sitter(cls, range: Range) -> 'TreeSitterRange':
        """Create from tree-sitter Range object."""
        return cls(
            start_point=range.start_point,
            end_point=range.end_point,
            start_byte=range.start_byte,
            end_byte=range.end_byte
        )


@dataclass
class TreeSitterError:
    """Represents a tree-sitter parsing error."""
    message: str
    range: TreeSitterRange
    node: Optional[Node] = None
    is_syntax_error: bool = True

    @property
    def line(self) -> int:
        """Get error line number."""
        return self.range.start_point.row

    @property
    def column(self) -> int:
        """Get error column number."""
        return self.range.start_point.column


@dataclass
class TreeSitterEdit:
    """Represents an edit operation in the source code."""
    start_byte: int
    old_end_byte: int
    new_end_byte: int
    start_point: Point
    old_end_point: Point
    new_end_point: Point


@dataclass
class TreeSitterResult:
    """Result of tree-sitter parsing."""

    def __init__(
        self,
        tree: Tree,
        language: str,
        errors: List[TreeSitterError],
        is_valid: bool,
        node_count: int,
        metadata: Dict[str, Any]
    ) -> None:
        """Initialize result.
        
        Args:
            tree: Parsed AST
            language: Language used for parsing
            errors: List of syntax errors
            is_valid: Whether parsing was successful
            node_count: Number of nodes in AST
            metadata: Additional metadata
        """
        self.tree = tree
        self.language = language
        self.errors = errors
        self.is_valid = is_valid
        self.node_count = node_count
        self.metadata = metadata
        
    @property
    def success(self) -> bool:
        """Whether parsing was successful."""
        return self.is_valid
        
    @property
    def ast(self) -> Tree:
        """Get the AST (alias for tree)."""
        return self.tree

    def get_root(self) -> Node:
        """Get the root node of the tree."""
        return self.tree.root_node

    def walk(self) -> TreeCursor:
        """Get a cursor for walking the tree."""
        return self.tree.walk()

    def print_tree(self, node: Optional[Node] = None, level: int = 0) -> None:
        """Print the AST structure for debugging."""
        if node is None:
            node = self.get_root()
        
        indent = "  " * level
        print(f"{indent}{node.type}: {node.text.decode('utf8') if node.text else ''}")
        print(f"{indent}Start: {node.start_point}, End: {node.end_point}")
        print(f"{indent}Error: {node.has_error}, Missing: {node.is_missing}")
        
        for child in node.children:
            self.print_tree(child, level + 1)

    def print_dot_graph(self, file_path: Union[str, Path]) -> None:
        """Write a DOT graph of the syntax tree."""
        with open(file_path, 'w') as f:
            self.tree.print_dot_graph(f)

    def copy(self) -> 'TreeSitterResult':
        """Create a shallow copy of the result."""
        return TreeSitterResult(
            tree=self.tree.copy(),
            language=self.language,
            errors=self.errors.copy(),
            is_valid=self.is_valid,
            node_count=self.node_count,
            metadata=self.metadata.copy()
        )


@dataclass
class TreeSitterLanguageBinding:
    """Represents a tree-sitter language binding."""
    name: str
    binding: int  # C binding pointer
    language: Language
    parser: Parser
    queries: Dict[str, Query] = field(default_factory=dict)

    def create_parser(self) -> Parser:
        """Create a new parser instance for this language."""
        parser = Parser()
        parser.set_language(self.language)
        return parser 