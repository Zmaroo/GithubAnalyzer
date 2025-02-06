"""Tree-sitter models for code analysis."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union

from tree_sitter import Language, Node, Parser, Point, Query, Range, Tree

from GithubAnalyzer.models.core.errors import ParserError, QueryError
from GithubAnalyzer.services.analysis.parsers.utils import NodeDict, NodeList
from GithubAnalyzer.utils.logging import get_logger

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

@dataclass
class TreeSitterServiceBase:
    """Base class for tree-sitter services."""
    language: Optional[str] = None
    parser: Optional[Parser] = None
    tree: Optional[Tree] = None
    
    def __post_init__(self):
        """Initialize the service."""
        logger.debug("Tree-sitter service initialized", extra={
            'context': {
                'operation': 'initialization',
                'language': self.language,
                'has_parser': self.parser is not None,
                'has_tree': self.tree is not None
            }
        })

@dataclass
class TreeSitterQuery:
    """Tree-sitter query with metadata."""
    query: Query
    language: str
    pattern_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the query."""
        logger.debug("Tree-sitter query initialized", extra={
            'context': {
                'operation': 'initialization',
                'language': self.language,
                'pattern_type': self.pattern_type,
                'metadata': self.metadata
            }
        })

@dataclass
class TreeSitterMatch:
    """Tree-sitter query match with metadata."""
    node: Node
    pattern_type: str
    captures: Dict[str, Node] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize the match."""
        logger.debug("Tree-sitter match initialized", extra={
            'context': {
                'operation': 'initialization',
                'pattern_type': self.pattern_type,
                'node_type': self.node.type,
                'capture_count': len(self.captures),
                'metadata': self.metadata
            }
        })
    
    def get_text(self, source_code: bytes) -> str:
        """Get text for this match from source code."""
        text = self.node.text.decode('utf8')
        logger.debug("Retrieved match text", extra={
            'context': {
                'operation': 'get_text',
                'pattern_type': self.pattern_type,
                'node_type': self.node.type,
                'text_length': len(text)
            }
        })
        return text
    
    def get_range(self) -> Range:
        """Get source range for this match."""
        range = Range(self.node.start_point, self.node.end_point)
        logger.debug("Retrieved match range", extra={
            'context': {
                'operation': 'get_range',
                'pattern_type': self.pattern_type,
                'node_type': self.node.type,
                'start': f"{range.start_point.row}:{range.start_point.column}",
                'end': f"{range.end_point.row}:{range.end_point.column}"
            }
        })
        return range

@dataclass
class TreeSitterEdit:
    """Tree-sitter edit operation."""
    start_byte: int
    old_end_byte: int
    new_end_byte: int
    start_point: Point
    old_end_point: Point
    new_end_point: Point
    
    def __post_init__(self):
        """Initialize the edit."""
        logger.debug("Tree-sitter edit initialized", extra={
            'context': {
                'operation': 'initialization',
                'start_byte': self.start_byte,
                'old_end_byte': self.old_end_byte,
                'new_end_byte': self.new_end_byte,
                'start_point': f"{self.start_point.row}:{self.start_point.column}",
                'old_end_point': f"{self.old_end_point.row}:{self.old_end_point.column}",
                'new_end_point': f"{self.new_end_point.row}:{self.new_end_point.column}"
            }
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert edit to dictionary."""
        edit_dict = {
            'start_byte': self.start_byte,
            'old_end_byte': self.old_end_byte,
            'new_end_byte': self.new_end_byte,
            'start_point': {'row': self.start_point.row, 'column': self.start_point.column},
            'old_end_point': {'row': self.old_end_point.row, 'column': self.old_end_point.column},
            'new_end_point': {'row': self.new_end_point.row, 'column': self.new_end_point.column}
        }
        logger.debug("Converted edit to dictionary", extra={
            'context': {
                'operation': 'to_dict',
                'edit': edit_dict
            }
        })
        return edit_dict 