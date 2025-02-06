"""Service for traversing syntax trees."""
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Union

from tree_sitter import (Language, Node, Parser, Point, Query, Range, Tree,
                         TreeCursor)
from tree_sitter_language_pack import get_parser

from GithubAnalyzer.models.analysis.types import NodeDict, NodeList
from GithubAnalyzer.models.core.errors import TraversalError
from GithubAnalyzer.models.core.traversal import (NodeContext, NodeRange,
                                                  TraversalResult,
                                                  TreeSitterTraversal)
from GithubAnalyzer.models.core.tree_sitter_core import (
    get_node_text, get_node_type, get_node_range, is_valid_node, node_to_dict
)
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class TraversalService:
    """Service for traversing syntax trees."""
    
    _traversal: TreeSitterTraversal = field(default_factory=TreeSitterTraversal)
    _operation_times: Dict[str, float] = field(default_factory=dict)
    _operation_counts: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize traversal service."""
        from GithubAnalyzer.services.core.base_service import BaseService
        super(BaseService, self).__init__()
        self._log("debug", "Traversal service initialized",
                operation="initialization")
        
    def _time_operation(self, operation: str) -> float:
        """Start timing an operation."""
        if operation not in self._operation_counts:
            self._operation_counts[operation] = 0
        self._operation_counts[operation] += 1
        return time.time()
        
    def _end_operation(self, operation: str, start_time: float):
        """End timing an operation."""
        duration = time.time() - start_time
        if operation not in self._operation_times:
            self._operation_times[operation] = 0
        self._operation_times[operation] += duration
        
        self._log("debug", f"Operation {operation} completed",
                operation=operation,
                duration_ms=duration * 1000,
                count=self._operation_counts[operation],
                total_time_ms=self._operation_times[operation] * 1000)
    
    def traverse_tree(self, tree: Tree, visit_fn: Optional[callable] = None) -> TraversalResult:
        """Traverse a syntax tree and collect nodes."""
        start_time = self._time_operation('traverse_tree')
        
        self._log("debug", "Starting tree traversal",
                operation="tree_traversal",
                root_type=tree.root_node.type)
                
        try:
            nodes = []
            for node in self._traversal.traverse(tree.root_node):
                node_info = self._traversal.get_node_info(node)
                if visit_fn:
                    visit_fn(node_info)
                nodes.append(node_info)
                
            duration = (time.time() - start_time) * 1000
            result = TraversalResult(
                nodes=nodes,
                is_valid=True,
                execution_time_ms=duration
            )
            
            self._log("debug", "Tree traversal completed",
                    operation="tree_traversal",
                    node_count=len(nodes),
                    duration_ms=duration)
                    
            return result
            
        except Exception as e:
            self._log("error", "Tree traversal failed",
                    operation="tree_traversal",
                    error=str(e))
                    
            return TraversalResult(
                is_valid=False,
                errors=[str(e)],
                execution_time_ms=(time.time() - start_time) * 1000
            )

    def find_nodes_by_type(self, node: Node, node_type: str) -> List[Node]:
        """Find all nodes of a specific type."""
        return self._traversal.find_nodes(
            node,
            lambda n: n.type == node_type
        )

    def find_nodes_by_text(self, node: Node, text: str) -> List[Node]:
        """Find nodes containing specific text."""
        return self._traversal.find_nodes(
            node,
            lambda n: n.text.decode('utf8').find(text) != -1
        )

    def get_node_path(self, node: Node) -> List[str]:
        """Get the path of node types from root to this node."""
        chain = self._traversal.get_ancestor_chain(node)
        return [n.type for n in chain]

    def get_node_depth(self, node: Node) -> int:
        """Get the depth of a node in the tree."""
        return len(self._traversal.get_ancestor_chain(node)) - 1

    def get_node_siblings(self, node: Node) -> List[Node]:
        """Get all siblings of a node (including itself)."""
        if not node.parent:
            return [node]
        return node.parent.children

    def get_previous_sibling(self, node: Node) -> Optional[Node]:
        """Get the previous sibling of a node."""
        siblings = self.get_node_siblings(node)
        index = siblings.index(node)
        return siblings[index - 1] if index > 0 else None

    def get_next_sibling(self, node: Node) -> Optional[Node]:
        """Get the next sibling of a node."""
        siblings = self.get_node_siblings(node)
        index = siblings.index(node)
        return siblings[index + 1] if index < len(siblings) - 1 else None

    def find_nodes_in_range(self, root: Node, range_obj: Range) -> List[Node]:
        """Find nodes in range using tree-sitter queries."""
        start_time = self._time_operation('find_nodes_in_range')
        try:
            if not root:
                self._log("error", "No root node provided")
                return []
                
            self._log("debug", "Finding nodes in range",
                    operation="find_nodes_in_range",
                    range={
                        'start': range_obj.start_point,
                        'end': range_obj.end_point
                    },
                    root_type=root.type)
            
            return self._traversal.find_nodes(
                root,
                lambda n: self.node_in_range(n, range_obj)
            )
            
        finally:
            self._end_operation('find_nodes_in_range', start_time)

    def node_in_range(self, node: Node, range_obj: Range) -> bool:
        """Check if node is within range."""
        try:
            if not node:
                return False
                
            node_range = NodeRange(
                start_point=Point(*node.start_point),
                end_point=Point(*node.end_point),
                start_byte=node.start_byte,
                end_byte=node.end_byte
            )
            
            in_range = (node_range.start_point >= range_obj.start_point and
                       node_range.end_point <= range_obj.end_point)
                       
            return in_range
            
        except Exception as e:
            self._log("error", "Error checking node range",
                    operation="node_in_range",
                    node_type=node.type if node else None,
                    error=str(e))
            return False

    def get_node_range(self, node: Node) -> NodeRange:
        """Get range spanned by node."""
        return NodeRange(
            start_point=Point(*node.start_point),
            end_point=Point(*node.end_point),
            start_byte=node.start_byte,
            end_byte=node.end_byte
        )

    def get_node_context(self, node: Node, context_lines: int = 2) -> NodeContext:
        """Get context around node including surrounding lines."""
        if not node:
            return NodeContext()
            
        try:
            # Get node info
            node_info = self._traversal.get_node_info(node)
            
            # Get line numbers
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            
            # Get source code lines
            text = node_info['text']
            source_lines = text.splitlines()
            
            # Get context lines
            start_context = max(0, start_line - context_lines)
            end_context = min(len(source_lines), end_line + context_lines + 1)
            
            context_before = source_lines[start_context:start_line]
            context_after = source_lines[end_line + 1:end_context]
            
            return NodeContext(
                node=node,
                start_line=start_line,
                end_line=end_line,
                context_before=context_before,
                context_after=context_after,
                text=text
            )
            
        except Exception as e:
            self._log("error", "Error getting node context",
                    operation="get_node_context",
                    node_type=node.type if node else None,
                    error=str(e))
            return NodeContext()

    def find_parent_of_type(self, node: Node, type_name: str) -> Optional[Node]:
        """Find closest parent node of given type."""
        chain = self._traversal.get_ancestor_chain(node)
        for parent in chain:
            if parent.type == type_name:
                return parent
        return None

    def find_error_nodes(self, node: Node) -> List[Node]:
        """Find all error nodes in the tree."""
        return self._traversal.find_nodes(
            node,
            lambda n: n.has_error or n.type == "ERROR"
        )

    def find_missing_nodes(self, node: Node) -> List[Node]:
        """Find all missing nodes in the tree."""
        return self._traversal.find_nodes(
            node,
            lambda n: n.is_missing
        )

    @staticmethod
    def walk_tree(node: Node) -> Generator[Node, None, None]:
        """Walk a tree using tree-sitter's native cursor API."""
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

    def get_node_info(self, node: Node) -> Dict[str, Any]:
        """Get comprehensive information about a node."""
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
        """Check if a node has any errors."""
        return node.has_error or node.type == "ERROR" or node.is_missing

    def verify_node(self, node: Node) -> bool:
        """Verify a node is valid and error-free."""
        if not node:
            return False
            
        # Check for errors in node and its children
        for n in self.walk_tree(node):
            if self.has_errors(n):
                return False
        return True

    def find_error_nodes(self, node: Node) -> List[Node]:
        """Find all error nodes in the tree."""
        error_nodes = []
        
        def check_node(n: Node):
            if n.has_error or n.type == "ERROR":
                error_nodes.append(n)
            for child in n.children:
                check_node(child)
                
        check_node(node)
        return error_nodes

    def find_missing_nodes(self, node: Node) -> List[Node]:
        """Find all missing nodes in the tree."""
        missing_nodes = []
        
        def check_node(n: Node):
            if n.is_missing:
                missing_nodes.append(n)
            for child in n.children:
                check_node(child)
                
        check_node(node)
        return missing_nodes 