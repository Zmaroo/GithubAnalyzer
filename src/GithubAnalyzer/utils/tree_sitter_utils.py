"""Analysis-specific utility functions for tree-sitter operations."""
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from tree_sitter import Node, Tree

from GithubAnalyzer.models.core.tree_sitter_core import (
    get_node_text, get_node_type, get_node_range, is_valid_node,
    node_to_dict, iter_children, get_node_hierarchy
)
from GithubAnalyzer.models.core.types import TreeSitterRange
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

# Re-export core functions
__all__ = [
    # Core functions
    'get_node_text', 'node_to_dict', 'is_valid_node',
    'get_node_type', 'get_node_range',
    
    # Analysis utilities
    'get_node_text_safe', 'find_common_ancestor',
    'get_node_hierarchy', 'iter_children',
    'get_node_children_text', 'get_node_parent_chain'
]

# Analysis-specific utilities
def get_node_text_safe(node: Optional[Node]) -> str:
    """Safely get text from a node, with additional error handling."""
    try:
        return get_node_text(node)
    except Exception as e:
        logger.error(f"Error getting node text: {e}")
        return ""

def get_node_children_text(node: Node) -> List[str]:
    """Get text from all children of a node."""
    if not node:
        return []
    return [get_node_text(child) for child in node.children]

def get_node_parent_chain(node: Node) -> List[Node]:
    """Get the chain of parent nodes."""
    if not node:
        return []
    chain = []
    current = node.parent
    while current:
        chain.append(current)
        current = current.parent
    return chain 

def find_common_ancestor(node1: Node, node2: Node) -> Optional[Node]:
    """Find common ancestor of two nodes.
    
    Args:
        node1: First tree-sitter node
        node2: Second tree-sitter node
        
    Returns:
        Common ancestor node if found, None otherwise
    """
    if not node1 or not node2:
        return None
        
    # Get ancestors of both nodes
    ancestors1 = []
    current = node1
    while current:
        ancestors1.append(current)
        current = current.parent
        
    ancestors2 = []
    current = node2
    while current:
        ancestors2.append(current)
        current = current.parent
        
    # Find first common ancestor
    for ancestor in ancestors1:
        if ancestor in ancestors2:
            return ancestor
            
    return None

def get_node_hierarchy(node: Node) -> List[str]:
    """Get the type hierarchy of a node."""
    if not node:
        return []
    hierarchy = []
    current = node
    while current:
        hierarchy.append(current.type)
        current = current.parent
    return hierarchy

def get_node_range(node: Node) -> TreeSitterRange:
    """Get range of a node.
    
    Args:
        node: Tree-sitter node
        
    Returns:
        TreeSitterRange containing start and end points
    """
    if not node:
        return TreeSitterRange(
            start_point=(0, 0),
            end_point=(0, 0),
            start_byte=0,
            end_byte=0
        )
    return TreeSitterRange(
        start_point=node.start_point,
        end_point=node.end_point,
        start_byte=node.start_byte,
        end_byte=node.end_byte
    ) 