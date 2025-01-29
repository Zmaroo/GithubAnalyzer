"""Tree-sitter traversal service for AST navigation."""
import time
import threading
from typing import List, Dict, Any, Optional, Union, TypeVar, Iterator, Generator, Tuple
from dataclasses import dataclass
from tree_sitter import Node, Tree, TreeCursor, Parser, Range, Point, Query

from tree_sitter_language_pack import get_binding, get_language, get_parser

from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.utils.logging import get_logger, LoggerFactory, StructuredFormatter
from GithubAnalyzer.utils.logging.tree_sitter_logging import TreeSitterLogHandler
from .utils import (
    get_node_text,
    node_to_dict,
    iter_children,
    get_node_hierarchy,
    find_common_ancestor,
    TreeSitterServiceBase
)
from .language_service import LanguageService

# Type variables for better type hints
T = TypeVar('T', bound=Node)

logger = get_logger(__name__)

@dataclass
class TreeSitterTraversal(TreeSitterServiceBase):
    """Utility class for traversing tree-sitter ASTs."""

    def __post_init__(self):
        """Initialize traversal with logging."""
        super().__post_init__()
        
        # Initialize language service
        self._language_service = LanguageService()
        
        # Log initialization
        self._logger.debug({
            "message": "TreeSitterTraversal initialized",
            "context": {
                'module': 'tree_sitter.traversal',
                'thread': threading.get_ident()
            }
        })

    def enable_parser_logging(self, parser: Parser) -> None:
        """Enable logging for a parser.
        
        Args:
            parser: Parser to enable logging for
        """
        # This method is kept for backward compatibility but delegates to the editor
        pass

    def disable_parser_logging(self, parser: Parser) -> None:
        """Disable logging for a parser.
        
        Args:
            parser: Parser to disable logging for
        """
        # This method is kept for backward compatibility but delegates to the editor
        pass

    def find_nodes_in_range(self, root: Node, range_obj: Range) -> List[Node]:
        """Find nodes in range using tree-sitter queries.
        
        Args:
            root: Root node to search in
            range_obj: Range to find nodes in
            
        Returns:
            List of nodes in the range
        """
        start_time = self._time_operation('find_nodes_in_range')
        try:
            if not root:
                self._logger.error({
                    "message": "No root node provided",
                    "context": {
                        'range': {
                            'start': range_obj.start_point,
                            'end': range_obj.end_point
                        },
                        'operation': 'find_nodes_in_range'
                    }
                })
                return []
                
            self._logger.debug({
                "message": "Finding nodes in range",
                "context": {
                    'range': {
                        'start': range_obj.start_point,
                        'end': range_obj.end_point
                    },
                    'root_type': root.type
                }
            })
            
            # Create query to find nodes in range
            query_str = f"""
                ({root.type}) @node
            """
            # Get language from root node's grammar name
            language = root.grammar_name
            if not language:
                self._logger.error("Could not determine language from root node")
                return []
                
            query = Query(self._language_service.get_language_object(language), query_str)
            captures = query.captures(root)
            nodes = [capture[0] for capture in captures]
                    
            self._logger.debug({
                "message": f"Found {len(nodes)} nodes in range",
                "context": {
                    'node_count': len(nodes),
                    'range': {
                        'start': range_obj.start_point,
                        'end': range_obj.end_point
                    }
                }
            })
            
            return nodes
            
        except Exception as e:
            self._logger.error({
                "message": "Error finding nodes in range",
                "context": {
                    'range': {
                        'start': range_obj.start_point,
                        'end': range_obj.end_point
                    },
                    'error': str(e)
                }
            })
            return []
        finally:
            self._end_operation('find_nodes_in_range', start_time)

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

    def find_node_at_point(self, root: Node, point: Point) -> Optional[Node]:
        """Find smallest node at point using tree-sitter's native API."""
        try:
            if not root:
                self._logger.error({
                    "message": "No root node provided",
                    "context": {
                        'point': point,
                        "operation": 'find_node_at_point'
                    }
                })
                return None
                
            self._logger.debug({
                "message": "Finding node at point",
                "context": {
                    'point': point,
                    'root_type': root.type,
                    'root_range': self.get_node_range(root)
                }
            })
            
            node = root.descendant_for_point_range(point, point)
            
            if node:
                self._logger.debug({
                    "message": "Found node at point",
                    "context": {
                        'node_type': node.type,
                        'node_range': self.get_node_range(node)
                    }
                })
            return node
            
        except Exception as e:
            self._logger.error({
                "message": "Error finding node at point",
                "context": {
                    'point': point,
                    'error': str(e),
                    'stack_trace': self._get_stack_trace()
                }
            })
            return None

    def node_in_range(self, node: Node, range_obj: Range) -> bool:
        """Check if node is within range.
        
        Args:
            node: Node to check
            range_obj: Range to check against
            
        Returns:
            True if node is within range
        """
        try:
            if not node:
                self._logger.debug({
                    "message": "Node is None in range check"
                })
                return False
                
            node_start = Point(*node.start_point)
            node_end = Point(*node.end_point)
            
            in_range = (node_start >= range_obj.start_point and
                       node_end <= range_obj.end_point)
                       
            self._logger.debug({
                "message": "Range check result",
                "context": {
                    'node_type': node.type,
                    'node_range': {
                        'start': node_start,
                        'end': node_end
                    },
                    'target_range': {
                        'start': range_obj.start_point,
                        'end': range_obj.end_point
                    },
                    'in_range': in_range
                }
            })
            
            return in_range
            
        except Exception as e:
            self._logger.error({
                "message": "Error checking node range",
                "context": {
                    'node_type': node.type if node else None,
                    'range': {
                        'start': range_obj.start_point,
                        'end': range_obj.end_point
                    }
                }
            })
            return False

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
            self._logger.error(f"Error finding parent of type: {e}")
            return None

    @staticmethod
    def get_node_range(node: Node) -> Dict[str, Any]:
        """Get range spanned by node."""
        return {
            'start_point': node.start_point,
            'end_point': node.end_point,
            'start_byte': node.start_byte,
            'end_byte': node.end_byte
        }

    @staticmethod
    def get_node_context(node: Node, context_lines: int = 2) -> Dict[str, Any]:
        """Get context around node including surrounding lines."""
        if not node:
            return {
                'node': None,
                'start_line': 0,
                'end_line': 0,
                'context_before': 0,
                'context_after': 0,
                'text': '',
                'range': None
            }
            
        start_line = max(0, node.start_point[0] - context_lines)
        end_line = node.end_point[0] + context_lines
        
        return {
            'node': node,
            'start_line': start_line,
            'end_line': end_line,
            'context_before': context_lines,
            'context_after': context_lines,
            'text': node.text.decode('utf8'),
            'range': TreeSitterTraversal.get_node_range(node)
        }

    @staticmethod
    def find_nodes_by_type(node: Node, node_type: str) -> List[Node]:
        """Find all nodes of a specific type."""
        nodes = []
        cursor = node.walk()
        
        while True:
            if cursor.node.type == node_type:
                nodes.append(cursor.node)
            
            if not cursor.goto_first_child():
                while not cursor.goto_next_sibling():
                    if not cursor.goto_parent():
                        return nodes
        return nodes

    @staticmethod
    def find_node_at_position(node: Node, point: Point) -> Optional[Node]:
        """Find the smallest node containing a point."""
        cursor = node.walk()
        
        while True:
            if (cursor.node.start_point <= point and 
                point <= cursor.node.end_point):
                
                if cursor.goto_first_child():
                    continue
                return cursor.node
            
            if not cursor.goto_next_sibling():
                if not cursor.goto_parent():
                    return None
        return None

    @staticmethod
    def find_child_by_field(node: Node, field_name: str) -> Optional[Node]:
        """Find a child node by its field name."""
        logger = TreeSitterLogHandler().logger
        try:
            return node.child_by_field_name(field_name)
        except Exception as e:
            logger.error(f"Error finding child by field {field_name}: {e}")
            return None

    def get_named_descendants(self, node: Node, start_byte: int = 0, end_byte: Optional[int] = None) -> List[Node]:
        """Get all named descendants in a byte range.
        
        Args:
            node: Root node to search in
            start_byte: Start byte offset
            end_byte: Optional end byte offset
            
        Returns:
            List of named descendant nodes
        """
        start_time = self._time_operation('get_named_descendants')
        
        try:
            # Get language from root node's grammar name
            language = node.grammar_name
            if not language:
                self._logger.error("Could not determine language from root node")
                return []
                
            # Create parser for getting node text
            parser = get_parser(language)
            
            # Get text content
            text = node.text.decode('utf8')
            
            # Default end_byte to text length if not specified
            if end_byte is None:
                end_byte = len(text.encode('utf8'))
                
            # Track visited nodes to avoid duplicates
            visited = set()
            nodes = []
            
            def visit_node(current: Node) -> None:
                if current.id in visited:
                    return
                visited.add(current.id)
                
                # Check if node is in range
                if (current.start_byte >= start_byte and 
                    current.end_byte <= end_byte and
                    current.is_named):
                    nodes.append(current)
                    
                # Visit children
                for child in current.children:
                    if (child.start_byte < end_byte and 
                        child.end_byte > start_byte):
                        visit_node(child)
                        
            visit_node(node)
            return nodes
            
        finally:
            self._end_operation('get_named_descendants', start_time)

    def get_node_at_byte_range(self, node: Optional[Node], start_byte: int, end_byte: int) -> Optional[Node]:
        """Get the smallest node that spans the given byte range."""
        if not node:
            self._logger.error("Cannot get node at byte range: Node is None")
            return None
            
        # Validate byte range
        if start_byte < 0 or end_byte < start_byte or end_byte > node.end_byte:
            self._logger.error(f"Invalid byte range: {start_byte} -> {end_byte} (node range: 0 -> {node.end_byte})")
            return None
            
        self._logger.debug(f"Finding node at byte range {start_byte} -> {end_byte}")
        
        # Get smallest descendant containing range
        found = node.descendant_for_byte_range(start_byte, end_byte)
        if not found:
            self._logger.warning("No node found containing byte range")
            return None
            
        # Walk up until we find a node that fully contains the range
        while found:
            self._logger.debug(f"Checking node {found.type} at bytes {found.start_byte} -> {found.end_byte}")
            if found.start_byte <= start_byte and found.end_byte >= end_byte:
                if not found.has_error and not found.is_missing:
                    self._logger.info(f"Found valid node: {found.type}")
                    return found
                else:
                    self._logger.warning(f"Found node has errors: {found.type}")
            found = found.parent
            
        self._logger.warning("No valid node found containing byte range")
        return None

    def verify_byte_range(self, node: Optional[Node], start_byte: int, end_byte: int, expected_text: str) -> bool:
        """Verify that a byte range in a node matches expected text."""
        if not node:
            self._logger.error("Cannot verify byte range: Node is None")
            return False
            
        # Validate byte range
        if start_byte < 0 or end_byte < start_byte or end_byte > node.end_byte:
            self._logger.error(f"Invalid byte range: {start_byte} -> {end_byte} (node range: 0 -> {node.end_byte})")
            return False
            
        # Get text at byte range
        try:
            text = node.text[start_byte - node.start_byte:end_byte - node.start_byte]
            actual_text = text.decode('utf8')
            if actual_text != expected_text:
                self._logger.error(f"Text mismatch at byte range. Expected: '{expected_text}', Got: '{actual_text}'")
                return False
            self._logger.debug(f"Text matches at byte range: '{actual_text}'")
            return True
        except Exception as e:
            self._logger.error(f"Error verifying byte range: {e}", exc_info=True)
            return False

    def get_byte_range_for_point_range(
        self,
        node: Optional[Node],
        start_point: Point,
        end_point: Point
    ) -> Optional[Tuple[int, int]]:
        """Convert a point range to a byte range.
        
        Args:
            node: The node containing the points
            start_point: Start row/column
            end_point: End row/column
            
        Returns:
            Tuple of (start_byte, end_byte) or None if invalid
            
        Note:
            - Returns None if points are out of bounds
            - Returns None if points are invalid
            - Uses tree-sitter's native point validation
        """
        if not node:
            return None
            
        # Validate points are in range
        if (start_point.row < 0 or start_point.column < 0 or
            end_point.row < start_point.row or
            (end_point.row == start_point.row and end_point.column < start_point.column) or
            start_point.row > node.end_point[0] or
            end_point.row > node.end_point[0]):
            return None
            
        # Find nodes at points
        start_node = node.descendant_for_point_range(start_point, start_point)
        if not start_node:
            return None
            
        end_node = node.descendant_for_point_range(end_point, end_point)
        if not end_node:
            return None
            
        # Get byte range
        return (start_node.start_byte, end_node.end_byte)

    @staticmethod
    def create_cursor_at_point(node: Node, point: tuple) -> Optional[TreeCursor]:
        """Create a cursor at a specific point in the tree."""
        logger = TreeSitterLogHandler().logger
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

    def walk_named_descendants(self, node: Node) -> Generator[Node, None, None]:
        """Walk through all named descendants of a node."""
        if not node:
            self._logger.warning("No node provided to walk_named_descendants")
            return
            
        self._logger.debug(f"Starting walk of named descendants from node type: {node.type}")
        cursor = node.walk()
        reached_root = False
        
        while not reached_root:
            if cursor.node.is_named:
                self._logger.debug(f"Found named node during walk: {cursor.node.type}")
                yield cursor.node
                
            if cursor.goto_first_child():
                continue
                
            if cursor.goto_next_sibling():
                continue
                
            while not reached_root:
                if not cursor.goto_parent():
                    reached_root = True
                    self._logger.debug("Reached root node, walk complete")
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
        """Get the path of nodes from root to this node."""
        path = []
        current = node
        while current:
            path.append(current)
            current = current.parent
        return list(reversed(path))

    @staticmethod
    def find_common_ancestor(node1: Node, node2: Node) -> Optional[Node]:
        """Find the lowest common ancestor of two nodes."""
        path1 = []
        current = node1
        while current:
            path1.append(current)
            current = current.parent

        current = node2
        while current:
            if current in path1:
                return current
            current = current.parent
        return None

    def traverse_tree(self, node: Node) -> Generator[Node, None, None]:
        """Traverse tree nodes."""
        yield node
        for child in node.children:
            yield from self.traverse_tree(child)

    def get_node_info(self, node: Node) -> Dict[str, Any]:
        """Get comprehensive information about a node.
        
        Args:
            node: Node to analyze
            
        Returns:
            Dict containing:
            - range: Node's byte and point range
            - type: Node type
            - grammar: Grammar name and id
            - children: Child counts (total, named)
            - descendants: Total descendant count
            - state: Parse state info
            - errors: Error status (has_error, is_error, is_missing)
            - changes: Whether node was edited
        """
        if not node:
            return {}
            
        return {
            'range': self.get_node_range(node),
            'type': node.type,
            'grammar': {
                'name': node.grammar_name,
                'id': node.grammar_id
            },
            'children': {
                'total': node.child_count,
                'named': node.named_child_count
            },
            'descendants': node.descendant_count,
            'state': {
                'parse_state': node.parse_state,
                'next_parse_state': node.next_parse_state
            },
            'errors': {
                'has_error': node.has_error,
                'is_error': node.is_error,
                'is_missing': node.is_missing,
                'is_extra': node.is_extra
            },
            'changes': node.has_changes
        }

    @staticmethod
    def has_errors(node: Node) -> bool:
        """Check if a node has any errors.
        
        Args:
            node: Node to check
            
        Returns:
            True if node has errors, is an error node, or is missing
        """
        return node.has_error or node.type == "ERROR" or node.is_missing

    def verify_node(self, node: Node) -> bool:
        """Verify a node is valid and error-free.
        
        Args:
            node: Node to verify
            
        Returns:
            True if node is valid and has no errors
        """
        if not node:
            return False
            
        # Check for errors in node and its children
        for n in self.walk_tree(node):
            if self.has_errors(n):
                return False
        return True

    def find_error_nodes(self, node: Node) -> List[Node]:
        """Find all error nodes in the tree.
        
        Args:
            node: Root node to search from
            
        Returns:
            List of nodes that have errors
        """
        error_nodes = []
        
        def check_node(n: Node):
            if n.has_error or n.type == "ERROR":
                error_nodes.append(n)
            for child in n.children:
                check_node(child)
                
        check_node(node)
        return error_nodes

    def find_missing_nodes(self, node: Node) -> List[Node]:
        """Find all missing nodes in the tree.
        
        Args:
            node: Root node to search from
            
        Returns:
            List of nodes that are missing
        """
        missing_nodes = []
        
        def check_node(n: Node):
            if n.is_missing:
                missing_nodes.append(n)
            for child in n.children:
                check_node(child)
                
        check_node(node)
        return missing_nodes

    def is_point_in_node_range(self, point: Point, node: Node) -> bool:
        """Check if a point is within a node's range.
        
        Args:
            point: The point to check
            node: The node to check against
            
        Returns:
            True if the point is within the node's range, False otherwise
        """
        start_point = node.start_point
        end_point = node.end_point
        
        # Check if point is within node's range
        if (point.row > start_point.row or 
            (point.row == start_point.row and point.column >= start_point.column)) and \
           (point.row < end_point.row or 
            (point.row == end_point.row and point.column <= end_point.column)):
            return True
            
        return False

    @staticmethod
    def find_nodes_by_text(node: Node, text: str) -> List[Node]:
        """Find nodes containing specific text."""
        nodes = []
        cursor = node.walk()
        
        while True:
            if cursor.node.text.decode('utf8').find(text) != -1:
                nodes.append(cursor.node)
            
            if not cursor.goto_first_child():
                while not cursor.goto_next_sibling():
                    if not cursor.goto_parent():
                        return nodes
        return nodes

    @staticmethod
    def get_node_text(node: Node) -> str:
        """Get the text content of a node."""
        return node.text.decode('utf8')

    @staticmethod
    def get_node_depth(node: Node) -> int:
        """Get the depth of a node in the tree."""
        depth = 0
        current = node
        while current.parent:
            depth += 1
            current = current.parent
        return depth

    def is_valid_position(self, node: Node, position: Point) -> bool:
        """Check if a position is valid within a node's range.
        
        Args:
            node: Node to check position against
            position: Position to validate
            
        Returns:
            True if position is valid
        """
        start_time = self._time_operation('is_valid_position')
        
        try:
            if not node:
                return False
                
            # Check for negative values
            if position.row < 0 or position.column < 0:
                return False
                
            # Get text content and split into lines
            text = node.text.decode('utf8')
            lines = text.split('\n')
            
            # Check row bounds
            if position.row >= len(lines):
                return False
                
            # Check column bounds for the specific row
            line = lines[position.row]
            if position.column > len(line):
                return False
                
            return True
            
        finally:
            self._end_operation('is_valid_position', start_time)

    def get_valid_symbols_at_error(self, node: Node) -> List[str]:
        """Get valid symbols that could appear at an error node.
        
        Uses Tree-sitter's LookaheadIterator to find valid symbols that could
        appear at the position of an error node. This is useful for:
        1. Providing better error messages
        2. Suggesting valid alternatives
        3. Validating edits before applying them
        
        Args:
            node: The error node to analyze
            
        Returns:
            List of valid symbol names that could appear at this position
        """
        if not node or not node.has_error:
            return []
            
        try:
            # Get the first leaf node state for errors
            cursor = node.walk()
            while cursor.goto_first_child():
                pass
                
            # Create lookahead iterator from this state
            lookahead = node.tree.language.lookahead_iterator(cursor.node.parse_state)
            
            # Get all valid symbol names
            valid_symbols = []
            for symbol_name in lookahead.iter_names():
                valid_symbols.append(symbol_name)
                
            self._logger.debug({
                "message": "Found valid symbols at error node",
                "context": {
                    "node_type": node.type,
                    "node_range": self.get_node_range(node),
                    "valid_symbols": valid_symbols
                }
            })
                
            return valid_symbols
            
        except Exception as e:
            self._logger.error({
                "message": "Error getting valid symbols",
                "context": {
                    "node_type": node.type,
                    "error": str(e)
                }
            })
            return []