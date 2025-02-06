"""Core tree-sitter utility functions."""
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from tree_sitter import Node, Tree

from GithubAnalyzer.models.core.types import TreeSitterRange
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

def get_node_text(node: Node) -> str:
    """Get text for a node.
    
    Args:
        node: Tree-sitter node
        
    Returns:
        Text content of the node
    """
    if not node:
        return ""
    try:
        return node.text.decode('utf8')
    except (AttributeError, UnicodeDecodeError):
        return str(node)

def get_node_text_safe(node: Optional[Node]) -> str:
    """Safely get text from a node, with additional error handling.
    
    Args:
        node: Tree-sitter node or None
        
    Returns:
        Text content of the node or empty string if node is invalid
    """
    try:
        return get_node_text(node)
    except Exception as e:
        logger.error(f"Error getting node text: {e}")
        return ""

def get_node_type(node: Node) -> str:
    """Get type of a node.
    
    Args:
        node: Tree-sitter node
        
    Returns:
        Type of the node
    """
    if not node:
        return ""
    return node.type

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

def is_valid_node(node: Node) -> bool:
    """Check if a node is valid.
    
    Args:
        node: Tree-sitter node
        
    Returns:
        True if node is valid, False otherwise
    """
    return (
        node is not None and
        hasattr(node, 'type') and
        hasattr(node, 'has_error') and
        not node.has_error
    )

def node_to_dict(node: Node) -> Dict[str, Any]:
    """Convert a node to a dictionary.
    
    Args:
        node: Tree-sitter node
        
    Returns:
        Dictionary representation of the node
    """
    if not node:
        return {}
        
    return {
        'type': node.type,
        'text': get_node_text(node),
        'start_point': node.start_point,
        'end_point': node.end_point,
        'start_byte': node.start_byte,
        'end_byte': node.end_byte,
        'children': [node_to_dict(child) for child in node.children]
    }

def iter_children(node: Node) -> List[Node]:
    """Get children of a node.
    
    Args:
        node: Tree-sitter node
        
    Returns:
        List of child nodes
    """
    if not node:
        return []
    return node.children

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