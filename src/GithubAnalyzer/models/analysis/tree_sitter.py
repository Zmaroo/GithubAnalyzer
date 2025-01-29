"""Tree-sitter models for code analysis."""
from typing import Dict, List, Optional, Any, Tuple, Union, TypedDict
from dataclasses import dataclass, field
from tree_sitter import Node, Tree, Point, Language, Parser

from GithubAnalyzer.utils.logging import get_logger
from GithubAnalyzer.models.core.errors import ParserError, QueryError
from GithubAnalyzer.services.analysis.parsers.utils import NodeDict, NodeList

logger = get_logger(__name__)

# Define proper type for node dictionaries
class NodeDict(TypedDict):
    """Type definition for node dictionary."""
    type: str
    text: str
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    children: List['NodeDict']

@dataclass
class TreeSitterResult:
    """Result of a tree-sitter parse operation."""
    tree: Optional[Tree] = None
    is_valid: bool = False
    errors: List[str] = field(default_factory=list)
    language: Optional[str] = None
    
    # Node collections
    functions: List[NodeDict] = field(default_factory=list)
    classes: List[NodeDict] = field(default_factory=list)
    imports: List[NodeDict] = field(default_factory=list)
    
    # Tree statistics
    node_count: int = 0
    error_count: int = 0
    depth: int = 0
    
    # Performance metrics
    parse_time_ms: float = 0
    query_time_ms: float = 0

@dataclass
class TreeSitterQueryMatch:
    """A single query match result."""
    pattern_index: int
    captures: Dict[str, Node]
    node: Node
    start_position: Point
    end_position: Point
    text: str = field(init=False)
    
    def __post_init__(self):
        """Initialize derived fields."""
        self.text = self.node.text.decode('utf8') if self.node else ""

@dataclass
class TreeSitterQueryResult:
    """Result of a tree-sitter query operation."""
    matches: List[TreeSitterQueryMatch] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    is_valid: bool = True
    execution_time_ms: float = 0
    pattern_count: int = 0
    match_count: int = 0

@dataclass
class TreeSitterRange:
    """Represents a range in the source code."""
    start_point: Point
    end_point: Point
    start_byte: int
    end_byte: int
    text: str

@dataclass
class TreeSitterEdit:
    """Represents a code edit operation."""
    old_range: TreeSitterRange
    new_range: TreeSitterRange
    old_text: str
    new_text: str
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    
    @property
    def is_deletion(self) -> bool:
        """Check if this edit is a deletion."""
        return bool(self.old_text and not self.new_text)
    
    @property
    def is_insertion(self) -> bool:
        """Check if this edit is an insertion."""
        return bool(not self.old_text and self.new_text)
    
    @property
    def is_modification(self) -> bool:
        """Check if this edit is a modification."""
        return bool(self.old_text and self.new_text) 