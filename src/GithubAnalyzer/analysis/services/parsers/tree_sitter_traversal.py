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
    """Utilities for traversing tree-sitter syntax trees."""

    @staticmethod
    def walk_tree(node: Node) -> Generator[Node, None, None]:
        """Walk a tree using tree-sitter's native cursor API.
        
        Args:
            node: Root node to start traversal from
            
        Yields:
            Each node in the tree in traversal order
        """
        if not node:
            return

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
    def find_node_at_point(root: Node, point: Point) -> Optional[Node]:
        """Find smallest node at point using tree-sitter's native API.
        
        Args:
            root: Root node to search in
            point: Point to find node at
            
        Returns:
            Node at point or None if not found
        """
        try:
            if not root:
                logger.error("Error finding node at point: No root node")
                return None
            return root.descendant_for_point_range(point, point)
        except Exception as e:
            logger.error(f"Error finding node at point: {e}")
            return None

    @staticmethod
    def find_nodes_in_range(root: Node, range_obj: Range) -> List[Node]:
        """Find nodes in range using tree-sitter's native API.
        
        Args:
            root: Root node to search in
            range_obj: Range to find nodes in
            
        Returns:
            List of nodes in range
        """
        try:
            if not root:
                logger.error("Error finding nodes in range: No root node")
                return []
            
            # Get smallest node containing range
            node = root.descendant_for_point_range(
                range_obj.start_point,
                range_obj.end_point
            )
            if not node:
                return []
                
            # Get all nodes within that node that overlap the range
            return [n for n in TreeSitterTraversal.walk_tree(node)
                   if TreeSitterTraversal.node_in_range(n, range_obj)]
        except Exception as e:
            logger.error(f"Error finding nodes in range: {e}")
            return []

    @staticmethod
    def node_in_range(node: Node, range_obj: Range) -> bool:
        """Check if node is within range.
        
        Args:
            node: Node to check
            range_obj: Range to check against
            
        Returns:
            True if node is within range
        """
        if not node:
            return False
            
        node_start = Point(*node.start_point)
        node_end = Point(*node.end_point)
        
        return (node_start >= range_obj.start_point and 
                node_end <= range_obj.end_point)

    def find_parent_of_type(self, node: Node, type_name: str) -> Optional[Node]:
        """Find closest parent node of given type.
        
        Args:
            node: Node to start from
            type_name: Type of parent to find
            
        Returns:
            Parent node of given type or None
        """
        try:
            if not node:
                return None
                
            current = node
            while current.parent:
                current = current.parent
                if current.type == type_name:
                    return current
            return None
        except Exception as e:
            logger.error(f"Error finding parent of type: {e}")
            return None

    @staticmethod
    def get_node_range(node: Node) -> Range:
        """Get range spanned by node.
        
        Args:
            node: Node to get range for
            
        Returns:
            Range object representing node's span
        """
        return Range(
            start_point=Point(*node.start_point),
            end_point=Point(*node.end_point),
            start_byte=node.start_byte,
            end_byte=node.end_byte
        )

    @staticmethod
    def get_node_context(node: Node, context_lines: int = 2) -> Dict[str, Any]:
        """Get context around node including surrounding lines.
        
        Args:
            node: Node to get context for
            context_lines: Number of lines before/after to include
            
        Returns:
            Dict with node and context information
        """
        if not node:
            return {
                'node': None,
                'start_line': 0,
                'end_line': 0,
                'context_before': 0,
                'context_after': 0
            }
            
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
    def find_nodes_by_type(root: Node, node_type: str) -> List[Node]:
        """Find all nodes of a specific type in the tree."""
        return [
            node for node in TreeSitterTraversal.walk_tree(root)
            if node.type == node_type
        ]

    @staticmethod
    def find_node_at_position(tree: Tree, position: Point) -> Optional[Node]:
        """Find node at position."""
        try:
            return tree.root_node.descendant_for_point_range(position, position)
        except Exception as e:
            logger.error(f"Error finding node at position {position}: {e}")
            return None

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
            # Check if point is within node's range
            point_row, point_col = point
            start_row, start_col = node.start_point
            end_row, end_col = node.end_point
            
            if not (start_row <= point_row <= end_row and
                   (point_row > start_row or point_col >= start_col) and
                   (point_row < end_row or point_col <= end_col)):
                return None
                
            cursor = node.walk()
            cursor.goto_first_child_for_point(point)
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
        """Walk through all named descendants of a node.
        
        Args:
            node: Node to walk
            
        Yields:
            Each named descendant node
        """
        if not node:
            return
            
        cursor = node.walk()
        reached_root = False
        
        while not reached_root:
            if cursor.node.is_named:
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

    def traverse_tree(self, node: Node) -> Generator[Node, None, None]:
        """Traverse tree nodes."""
        yield node
        for child in node.children:
            yield from self.traverse_tree(child) 