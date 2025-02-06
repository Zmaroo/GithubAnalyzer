"""Core tree-sitter traversal functionality."""
from dataclasses import dataclass, field
from typing import (Any, Dict, Iterator, List, Optional, Set, Tuple, TypeVar,
                    Union)

from tree_sitter import Node, Tree

from GithubAnalyzer.models.core.ast import NodeDict, NodeList
from GithubAnalyzer.models.core.base_model import BaseModel
from GithubAnalyzer.models.core.errors import TraversalError
from GithubAnalyzer.models.core.tree_sitter_core import (
    get_node_text, get_node_type, get_node_range, is_valid_node,
    node_to_dict, iter_children, get_node_hierarchy
)
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound=Node)

@dataclass
class NodeRange(BaseModel):
    """Range information for a node in the AST."""
    start_point: Tuple[int, int]  # (line, column)
    end_point: Tuple[int, int]    # (line, column)
    start_byte: int
    end_byte: int
    
    def contains(self, other: 'NodeRange') -> bool:
        """Check if this range contains another range."""
        return (self.start_byte <= other.start_byte and
                self.end_byte >= other.end_byte)
    
    def overlaps(self, other: 'NodeRange') -> bool:
        """Check if this range overlaps with another range."""
        return not (self.end_byte < other.start_byte or
                   self.start_byte > other.end_byte)

@dataclass
class NodeContext(BaseModel):
    """Context information for a node in the AST."""
    node_id: str
    node_type: str
    node_text: str
    range: NodeRange
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    visited: bool = False
    
    def __post_init__(self):
        """Initialize node context."""
        super().__post_init__()
        self._log("debug", "Node context initialized",
                node_id=self.node_id,
                node_type=self.node_type)
    
    def add_child(self, child_id: str):
        """Add a child node ID."""
        if child_id not in self.children:
            self.children.append(child_id)
            self._log("debug", "Added child node",
                    node_id=self.node_id,
                    child_id=child_id)
    
    def set_parent(self, parent_id: str):
        """Set the parent node ID."""
        self.parent_id = parent_id
        self._log("debug", "Set parent node",
                node_id=self.node_id,
                parent_id=parent_id)
    
    def mark_visited(self):
        """Mark this node as visited."""
        self.visited = True
        self._log("debug", "Marked node as visited",
                node_id=self.node_id)
    
    def add_attribute(self, key: str, value: Any):
        """Add an attribute to this node."""
        self.attributes[key] = value
        self._log("debug", "Added node attribute",
                node_id=self.node_id,
                key=key)

@dataclass
class TraversalResult(BaseModel):
    """Result of a tree traversal operation."""
    nodes: List[NodeDict] = field(default_factory=list)
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    
    def __post_init__(self):
        """Initialize traversal result."""
        super().__post_init__()
        self._log("debug", "Traversal result initialized",
                node_count=len(self.nodes),
                is_valid=self.is_valid,
                error_count=len(self.errors))

@dataclass
class TreeSitterTraversal:
    """Core tree-sitter traversal functionality."""
    
    _visited: Set[int] = field(default_factory=set)
    _node_cache: Dict[int, NodeDict] = field(default_factory=dict)
    
    def traverse(self, node: Node, visit_once: bool = True) -> Iterator[Node]:
        """Traverse a tree-sitter node.
        
        Args:
            node: Node to traverse
            visit_once: Whether to visit each node only once
            
        Yields:
            Each node in the traversal
            
        Raises:
            TraversalError: If traversal fails
        """
        if not is_valid_node(node):
            raise TraversalError("Invalid node for traversal")
            
        try:
            # Reset visited set if not visiting nodes multiple times
            if visit_once:
                self._visited = set()
                
            # Start with current node
            stack = [node]
            while stack:
                current = stack.pop()
                
                # Skip if already visited
                if visit_once and id(current) in self._visited:
                    continue
                    
                # Mark as visited and yield
                if visit_once:
                    self._visited.add(id(current))
                yield current
                
                # Add children to stack
                stack.extend(reversed(list(iter_children(current))))
                
        except Exception as e:
            raise TraversalError(f"Traversal failed: {e}")
            
    def get_node_info(self, node: Node) -> NodeDict:
        """Get detailed information about a node.
        
        Args:
            node: Node to get info for
            
        Returns:
            Dictionary with node information
            
        Raises:
            TraversalError: If node is invalid
        """
        if not is_valid_node(node):
            raise TraversalError("Invalid node")
            
        # Check cache first
        node_id = id(node)
        if node_id in self._node_cache:
            return self._node_cache[node_id]
            
        try:
            # Get basic node info
            info = node_to_dict(node)
            
            # Add hierarchy information
            info['hierarchy'] = get_node_hierarchy(node)
            
            # Add text content
            info['text'] = get_node_text(node)
            
            # Add position information
            info['range'] = get_node_range(node)
            
            # Cache and return
            self._node_cache[node_id] = info
            return info
            
        except Exception as e:
            raise TraversalError(f"Failed to get node info: {e}")
            
    def find_nodes(
        self,
        root: Node,
        predicate: callable,
        max_depth: Optional[int] = None,
        max_nodes: Optional[int] = None
    ) -> List[Node]:
        """Find nodes matching a predicate.
        
        Args:
            root: Root node to search from
            predicate: Function that takes a node and returns bool
            max_depth: Maximum depth to search
            max_nodes: Maximum number of nodes to return
            
        Returns:
            List of matching nodes
            
        Raises:
            TraversalError: If search fails
        """
        if not is_valid_node(root):
            raise TraversalError("Invalid root node")
            
        try:
            matches = []
            current_depth = 0
            
            def _search(node: Node, depth: int) -> None:
                if max_depth is not None and depth > max_depth:
                    return
                if max_nodes is not None and len(matches) >= max_nodes:
                    return
                    
                if predicate(node):
                    matches.append(node)
                    
                for child in iter_children(node):
                    _search(child, depth + 1)
                    
            _search(root, current_depth)
            return matches
            
        except Exception as e:
            raise TraversalError(f"Node search failed: {e}")
            
    def get_ancestor_chain(self, node: Node) -> List[Node]:
        """Get chain of ancestors for a node.
        
        Args:
            node: Node to get ancestors for
            
        Returns:
            List of ancestor nodes from root to node
            
        Raises:
            TraversalError: If node is invalid
        """
        if not is_valid_node(node):
            raise TraversalError("Invalid node")
            
        try:
            chain = []
            current = node
            
            while current:
                chain.append(current)
                current = current.parent
                
            return list(reversed(chain))
            
        except Exception as e:
            raise TraversalError(f"Failed to get ancestor chain: {e}")
            
    def clear_cache(self) -> None:
        """Clear the node cache."""
        self._node_cache.clear()
        self._visited.clear() 