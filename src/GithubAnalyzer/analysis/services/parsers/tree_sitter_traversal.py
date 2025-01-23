"""Tree-sitter node traversal utilities."""

from typing import List, Optional, Generator, Dict, Any, Tuple, Union, TypeVar
import logging
from dataclasses import dataclass

from tree_sitter import (
    Node,
    TreeCursor,
    Point,
    Range,
    Query,
    Tree,
    Language,
    Parser
)

from src.GithubAnalyzer.core.config.settings import settings
from src.GithubAnalyzer.core.models.errors import ParserError

logger = logging.getLogger(__name__)

# Type variables for better type hints
T = TypeVar('T', bound=Node)

class TreeSitterTraversal:
    """Utilities for traversing Tree-sitter nodes."""
    
    @staticmethod
    def walk_tree(node: Node) -> Generator[Node, None, None]:
        """Walk through all nodes in the tree using cursor."""
        cursor = node.walk()
        
        reached_root = False
        while not reached_root:
            yield cursor.node
            
            if cursor.goto_first_child():
                continue
                
            if cursor.goto_next_sibling():
                continue
                
            while not reached_root:
                if not cursor.goto_parent():
                    reached_root = True
                    break
                    
                if cursor.goto_next_sibling():
                    break

    @staticmethod
    def find_nodes_by_type(root: Node, node_type: str) -> List[Node]:
        """Find all nodes of a specific type in the tree."""
        return [
            node for node in TreeSitterTraversal.walk_tree(root)
            if node.type == node_type
        ]

    @staticmethod
    def find_parent_of_type(node: Node, parent_type: str) -> Optional[Node]:
        """Find the nearest parent node of a specific type."""
        current = node.parent
        while current:
            if current.type == parent_type:
                return current
            current = current.parent
        return None

    @staticmethod
    def find_node_at_position(tree: Tree, position: Point) -> Optional[Node]:
        """Find node at position."""
        node = tree.root_node
        while node:
            for child in node.children:
                if child.start_point <= position <= child.end_point:
                    node = child
                    break
            else:
                break
        return node

    @staticmethod
    def get_node_context(node: Node, context_lines: int = 2) -> Dict[str, Any]:
        """Get source context around a node."""
        start_line = max(0, node.start_point[0] - context_lines)
        end_line = node.end_point[0] + context_lines
        
        return {
            'node': node,
            'start_line': start_line,
            'end_line': end_line,
            'context_before': context_lines,
            'context_after': context_lines
        }

    @staticmethod
    def find_child_by_field(node: Node, field_name: str) -> Optional[Node]:
        """Find a child node by its field name."""
        try:
            return node.child_by_field_name(field_name)
        except Exception as e:
            logger.error(f"Error finding child by field {field_name}: {e}")
            return None

    @staticmethod
    def get_named_descendants(node: Node, start_byte: int, end_byte: int) -> List[Node]:
        """Get named descendants in a byte range."""
        try:
            return node.named_descendant_for_byte_range(start_byte, end_byte)
        except Exception as e:
            logger.error(f"Error getting named descendants: {e}")
            return []

    @staticmethod
    def create_cursor_at_point(node: Node, point: tuple) -> Optional[TreeCursor]:
        """Create a cursor at a specific point in the tree."""
        try:
            cursor = node.walk()
            if cursor.goto_first_child_for_point(point):
                return cursor
        except Exception as e:
            logger.error(f"Error creating cursor at point {point}: {e}")
        return None 

    @staticmethod
    def walk_descendants(node: Node) -> Generator[Node, None, None]:
        """Walk through all descendants of a node."""
        for child in node.children:
            yield child
            yield from TreeSitterTraversal.walk_descendants(child)

    @staticmethod
    def walk_named_descendants(node: Node) -> Generator[Node, None, None]:
        """Walk through all named descendants of a node."""
        for child in node.named_children:
            if child.is_named:
                yield child
                yield from TreeSitterTraversal.walk_named_descendants(child)

    @staticmethod
    def find_node_at_point(root: Node, point: Point) -> Optional[Node]:
        """Find the smallest node that contains the given point."""
        try:
            return root.descendant_for_point_range(point, point)
        except Exception as e:
            logger.error(f"Error finding node at point {point}: {e}")
            return None

    @staticmethod
    def find_nodes_in_range(root: Node, range: Range) -> List[Node]:
        """Find all nodes within a given range."""
        try:
            start_node = root.descendant_for_point_range(range.start_point, range.start_point)
            end_node = root.descendant_for_point_range(range.end_point, range.end_point)
            
            if not (start_node and end_node):
                return []
                
            nodes = []
            current = start_node
            while current and current != end_node:
                nodes.append(current)
                current = TreeSitterTraversal.get_next_node(current)
                
            if end_node:
                nodes.append(end_node)
                
            return nodes
        except Exception as e:
            logger.error(f"Error finding nodes in range {range}: {e}")
            return []

    @staticmethod
    def get_next_node(node: Node) -> Optional[Node]:
        """Get the next node in traversal order."""
        # Try to get first child
        if node.child_count > 0:
            return node.children[0]
            
        # Try to get next sibling
        if node.next_sibling:
            return node.next_sibling
            
        # Go up until we find a parent with a next sibling
        current = node
        while current.parent:
            if current.parent.next_sibling:
                return current.parent.next_sibling
            current = current.parent
            
        return None

    @staticmethod
    def get_node_path(node: Node) -> List[Node]:
        """Get path from root to node."""
        path = []
        current = node
        while current:
            path.insert(0, current)
            current = current.parent
        return path

    @staticmethod
    def find_common_ancestor(node1: Node, node2: Node) -> Optional[Node]:
        """Find the lowest common ancestor of two nodes."""
        path1 = TreeSitterTraversal.get_node_path(node1)
        path2 = TreeSitterTraversal.get_node_path(node2)
        
        # Find last common node in paths
        common_ancestor = None
        for n1, n2 in zip(path1, path2):
            if n1 != n2:
                break
            common_ancestor = n1
            
        return common_ancestor

    @staticmethod
    def get_node_range(node: Node) -> Range:
        """Get the range covered by a node."""
        return Range(
            start_point=node.start_point,
            end_point=node.end_point,
            start_byte=node.start_byte,
            end_byte=node.end_byte
        ) 

    def traverse_tree(self, node: Node) -> Generator[Node, None, None]:
        """Traverse tree nodes."""
        yield node
        for child in node.children:
            yield from self.traverse_tree(child)

    def find_parent_of_type(self, node: Node, type_name: str) -> Optional[Node]:
        """Find parent node of specific type."""
        current = node.parent
        while current:
            if current.type == type_name:
                return current
            current = current.parent
        return None 