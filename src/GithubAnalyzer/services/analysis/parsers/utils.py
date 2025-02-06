"""Utility functions and types for parser services."""
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from tree_sitter import Language, Node, Parser, Query, Tree

from GithubAnalyzer.models.analysis.types import (LanguageId, NodeDict,
                                                  NodeList, QueryPattern,
                                                  QueryResult)
from GithubAnalyzer.utils.logging import get_logger, get_tree_sitter_logger

# Common type aliases
LanguageId = str
QueryPattern = str
NodeDict = Dict[str, Any]
NodeList = List[Node]
QueryResult = Dict[str, NodeList]

logger = get_logger(__name__)

@dataclass
class TreeSitterServiceBase:
    """Base class for tree-sitter services with common functionality."""
    
    _operation_times: dict = field(default_factory=dict)

    def __post_init__(self):
        """Initialize tree-sitter service."""
        self._operation_times = {}
    
    def _time_operation(self, operation_name: str) -> float:
        """Record timing for an operation.
        
        Args:
            operation_name: Name of the operation to time
            
        Returns:
            Start time for the operation
        """
        start_time = time.time()
        if operation_name not in self._operation_times:
            self._operation_times[operation_name] = []
        return start_time
        
    def _end_operation(self, operation_name: str, start_time: float) -> None:
        """End timing for an operation and log metrics.
        
        Args:
            operation_name: Name of the operation
            start_time: Start time from _time_operation
        """
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        self._operation_times[operation_name].append(duration)
        
        # Calculate statistics
        times = self._operation_times[operation_name]
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        self._log("debug", f"Operation timing: {operation_name}",
                operation=operation_name,
                duration_ms=duration,
                avg_duration_ms=avg_time,
                max_duration_ms=max_time,
                call_count=len(times),
                type="query",
                source="tree-sitter")

    def _log(self, level: str, message: str, **kwargs):
        logger = get_logger(__name__)
        getattr(logger, level)(message, extra={'context': kwargs})

def get_node_text(node: Optional[Node]) -> str:
    """Get text from a node."""
    if not node:
        return ""
    try:
        return node.text.decode('utf8')
    except (AttributeError, UnicodeDecodeError):
        return str(node)

def node_to_dict(node: Node) -> Dict[str, Any]:
    """Convert a node to a dictionary."""
    return {
        'type': node.type,
        'text': get_node_text(node),
        'start_point': node.start_point,
        'end_point': node.end_point,
        'start_byte': node.start_byte,
        'end_byte': node.end_byte
    }

def iter_children(node: Node) -> List[Node]:
    """Get all children of a node."""
    return list(node.children)

def get_node_hierarchy(node: Node) -> List[str]:
    """Get the type hierarchy of a node."""
    hierarchy = []
    current = node
    while current:
        hierarchy.append(current.type)
        current = current.parent
    return hierarchy

def find_common_ancestor(node1: Node, node2: Node) -> Optional[Node]:
    """Find the common ancestor of two nodes."""
    if not node1 or not node2:
        return None
        
    ancestors1 = set()
    current = node1
    while current:
        ancestors1.add(current)
        current = current.parent
        
    current = node2
    while current:
        if current in ancestors1:
            return current
        current = current.parent
        
    return None

def is_valid_node(node: Optional[Node]) -> bool:
    """Check if a node is valid."""
    return node is not None and not node.has_error

def get_node_type(node: Optional[Node]) -> str:
    """Get node type safely."""
    return node.type if node else ""

def get_node_text_safe(node: Optional[Node]) -> str:
    """Get node text safely."""
    if not node:
        return ""
    try:
        return node.text.decode('utf8')
    except (AttributeError, UnicodeDecodeError):
        return str(node)

def get_node_range(node: Node) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Get the range of a node as ((start_row, start_col), (end_row, end_col))."""
    return (node.start_point, node.end_point)

def get_node_children_text(node: Node) -> List[str]:
    """Get text of all child nodes."""
    return [get_node_text(child) for child in node.children]

def get_node_parent_chain(node: Node) -> List[Node]:
    """Get chain of parent nodes up to root."""
    chain = []
    current = node
    while current:
        chain.append(current)
        current = current.parent
    return chain 