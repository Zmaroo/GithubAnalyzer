"""Tree-sitter query handler."""
from tree_sitter import Query, Node, Tree, QueryError, Language, Point
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from tree_sitter_language_pack import get_binding, get_language, get_parser
from src.GithubAnalyzer.analysis.services.parsers.query_patterns import (
    get_query_pattern,
    get_optimization_settings,
    QueryOptimizationSettings
)
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_logging import TreeSitterLogHandler
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_traversal import TreeSitterTraversal
import logging

class TreeSitterQueryHandler:
    """Handles tree-sitter query operations."""
    
    def __init__(self, logger: TreeSitterLogHandler):
        """Initialize query handler."""
        self.logger = logger
        self._pattern_queries = {}
        self._traversal = TreeSitterTraversal()
        self._disabled_captures: Set[str] = set()
        self._disabled_patterns: Set[int] = set()
        
        try:
            self._language = get_language('python')  # Initialize with Python language
            self.logger.info("Initialized Python language support")
        except Exception as e:
            self.logger.error(f"Failed to initialize language: {str(e)}")
            self._language = None
        
        # Core query patterns for Python
        self._ERROR_PATTERN = """
            (ERROR) @error
        """
        
        self._MISSING_PATTERN = """
            (missing) @missing
        """
        
        self._FUNCTION_PATTERN = """
            (function_definition
                name: (identifier) @function.name
                parameters: (parameters) @function.parameters
                body: (block) @function.body) @function
        """
        
        self._CLASS_PATTERN = """
            (class_definition
                name: (identifier) @class.name
                body: (block) @class.body) @class
        """
        
        self._METHOD_PATTERN = """
            (function_definition
                name: (identifier) @method.name
                parameters: (parameters) @method.parameters
                body: (block) @method.body) @method
            (#has-parent? @method class_definition)
        """
        
        self._IMPORT_PATTERN = """
            (import_statement) @import
            (import_from_statement) @import
        """
        
        self._CALL_PATTERN = """
            (call
                function: [
                    (identifier) @call.name
                    (attribute 
                        object: (identifier) @call.object
                        attribute: (identifier) @call.method)
                ]) @call
        """
        
        self._ATTRIBUTE_PATTERN = """
            (attribute
                object: (identifier) @attribute.object
                attribute: (identifier) @attribute.name) @attribute
        """
        
        self._STRING_PATTERN = """
            [(string) (string_content)] @string
        """
        
        self._COMMENT_PATTERN = """
            (comment) @comment
        """

    def create_query(self, query_string: str) -> Query:
        """Create a tree-sitter query from a string."""
        try:
            if not self._language:
                raise QueryError("Language not initialized")
            return Query(self._language, query_string)
        except Exception as e:
            self.logger.error(f"Failed to create query: {str(e)}")
            raise

    def disable_capture(self, capture: str) -> None:
        """Disable a capture in future queries.
        
        Args:
            capture: Name of capture to disable
        """
        self._disabled_captures.add(capture)

    def disable_pattern(self, pattern_index: int) -> None:
        """Disable a pattern in future queries.
        
        Args:
            pattern_index: Index of pattern to disable
        """
        self._disabled_patterns.add(pattern_index)

    def get_query_stats(self, query: Query) -> Dict[str, Any]:
        """Get statistics about a query.

        Args:
            query: Query to get statistics for

        Returns:
            Dictionary containing query statistics:
                - pattern_count: Number of patterns in query
                - match_limit: Maximum number of matches allowed
                - timeout_micros: Query timeout in microseconds
                - did_exceed_match_limit: Whether match limit was exceeded (boolean)
        """
        try:
            return {
                "pattern_count": query.pattern_count,
                "match_limit": query.match_limit,
                "timeout_micros": query.timeout_micros,
                "did_exceed_match_limit": bool(query.did_exceed_match_limit)
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get query stats: {str(e)}")
            raise QueryError(str(e))

    def execute_query(self, query: Query, node: Node) -> Dict[str, List[Node]]:
        """Execute a query on a node and return captures."""
        if not node:
            raise ValueError("Cannot execute query on None node")

        try:
            # query.captures() returns a dict directly in v24
            captures = query.captures(node)
            return {
                name: nodes for name, nodes in captures.items()
                if name not in self._disabled_captures
            }
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}", exc_info=True)
            raise

    def get_matches(self, query: Query, node: Node) -> List[Dict[str, List[Node]]]:
        """Get matches from a query execution."""
        try:
            # query.matches() returns [(pattern_idx, match_dict), ...]
            matches = query.matches(node)
            return [
                match for pattern_idx, match in matches
                if pattern_idx not in self._disabled_patterns
            ]
        except Exception as e:
            self.logger.error(f"Failed to get matches: {e}", exc_info=True)
            raise

    def configure_query(self, query: Query, settings: QueryOptimizationSettings):
        """Configure query with optimization settings."""
        try:
            if settings.match_limit:
                query.match_limit = settings.match_limit
            if settings.timeout_micros:
                query.timeout_micros = settings.timeout_micros
        except Exception as e:
            self.logger.warning(f"Query configuration settings are no longer supported: {str(e)}")

    def get_pattern_info(self, query: Query, pattern_index: int) -> Dict[str, Any]:
        """Get information about a query pattern."""
        return {
            "is_rooted": query.is_pattern_rooted(pattern_index),
            "is_non_local": query.is_pattern_non_local(pattern_index),
            "assertions": query.pattern_assertions(pattern_index),
            "settings": query.pattern_settings(pattern_index)
        }

    def _get_pattern_query(self, pattern_type: str) -> Optional[str]:
        """Get query string for a pattern type."""
        patterns = {
            "function": "(function_definition) @function",
            "class": "(class_definition) @class",
            "string": "(string) @string",
            "comment": "(comment) @comment",
            "call": "(call) @call",
            "attribute": "(attribute) @attribute",
            "import": "(import_statement) @import",
            "ERROR": "(ERROR) @error"
        }
        return patterns.get(pattern_type)

    def _process_captures(self, captures: Dict[str, List[Node]]) -> Dict[str, List[Node]]:
        """Process captures into a dictionary mapping capture names to node lists.

        Args:
            captures: Dictionary mapping capture names to lists of nodes from tree-sitter

        Returns:
            Dictionary mapping capture names to lists of nodes
        """
        return captures  # Tree-sitter already returns the format we want

    def find_nodes(self, tree: Tree, pattern_type: str) -> List[Node]:
        """Find nodes matching a pattern type."""
        if pattern_type not in self._pattern_queries:
            query_string = self._get_pattern_query(pattern_type)
            if not query_string:
                self.logger.warning(f"Unknown pattern type: {pattern_type}")
                return []
            self._pattern_queries[pattern_type] = self.create_query(query_string)

        query = self._pattern_queries[pattern_type]
        captures = self.execute_query(query, tree.root_node)
        return [node for nodes in captures.values() for node in nodes]

    def find_missing_nodes(self, node: Node) -> List[Node]:
        """Find missing nodes using query pattern matching."""
        query = self.create_query("""
            (missing) @missing
            (#is? @missing "missing")
        """)
        if not query:
            return []
        captures = query.captures(node)
        return captures.get('missing', [])

    def find_error_nodes(self, node: Node) -> List[Node]:
        """Find error nodes using query pattern matching."""
        query = self.create_query("""
            (ERROR) @error
            (#is? @error "error")
        """)
        if not query:
            return []
        captures = query.captures(node)
        return captures.get('error', [])

    def validate_syntax(self, node: Node) -> Tuple[bool, List[str]]:
        """Validate syntax using error and missing node queries.
        
        Args:
            node: Node to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Check for error nodes
        error_query = self.create_query(self._ERROR_PATTERN)
        if error_query:
            error_captures = error_query.captures(node)
            for error_node in error_captures.get('error', []):
                errors.append(f"Syntax error at line {error_node.start_point[0] + 1}, column {error_node.start_point[1]}")
                
        # Check for missing nodes
        missing_query = self.create_query(self._MISSING_PATTERN)
        if missing_query:
            missing_captures = missing_query.captures(node)
            for missing_node in missing_captures.get('missing', []):
                errors.append(f"Missing node at line {missing_node.start_point[0] + 1}, column {missing_node.start_point[1]}")
                
        # Check for general tree errors
        if node.has_error:
            errors.append("Tree contains syntax errors")
            
        return len(errors) == 0, errors

    def find_functions(self, node: Node) -> List[Dict[str, Node]]:
        """Find function definitions with their components.
        
        Args:
            node: Root node to search in
            
        Returns:
            List of dictionaries containing function components:
                - function.def: Complete function node
                - function.name: Function name node
                - function.params: Parameters node
                - function.body: Function body node
        """
        query = self.create_query(self._FUNCTION_PATTERN)
        if not query:
            return []
            
        try:
            # Get all captures at once
            captures = query.captures(node)
            
            # Group captures by function definition
            functions = []
            current_func = {}
            
            # Process captures to group by function
            for capture_name, nodes in captures.items():
                for node in nodes:
                    if capture_name == 'function.def':
                        if current_func:
                            functions.append(current_func)
                        current_func = {'function.def': node}
                    else:
                        current_func[capture_name] = node
                        
            # Add last function if exists
            if current_func:
                functions.append(current_func)
                
            return functions
        except Exception as e:
            self.logger.error(f"Failed to find functions: {str(e)}")
            return []

    def find_classes(self, node: Node) -> List[Dict[str, Node]]:
        """Find class definitions with their components.
        
        Args:
            node: Root node to search in
            
        Returns:
            List of dictionaries containing class components:
                - class.def: Complete class node
                - class.name: Class name node
                - class.body: Class body node
        """
        query = self.create_query(self._CLASS_PATTERN)
        if not query:
            return []
            
        try:
            # Get all captures at once
            captures = query.captures(node)
            
            # Group captures by class definition
            classes = []
            current_class = {}
            
            # Process captures to group by class
            for capture_name, nodes in captures.items():
                for node in nodes:
                    if capture_name == 'class.def':
                        if current_class:
                            classes.append(current_class)
                        current_class = {'class.def': node}
                    else:
                        current_class[capture_name] = node
                        
            # Add last class if exists
            if current_class:
                classes.append(current_class)
                
            return classes
        except Exception as e:
            self.logger.error(f"Failed to find classes: {str(e)}")
            return []

    def find_nodes_by_type(self, node: Node, node_type: str) -> List[Node]:
        """Find nodes of a specific type using query pattern."""
        pattern = f"({node_type}) @target"
        query = self.create_query(pattern)
        if not query:
            return []
            
        return [capture[0] for capture in query.captures(node)]

    def is_valid_node(self, node: Node) -> bool:
        """Check if a node is valid (no errors or missing parts)."""
        if not node:
            return False
            
        is_valid, _ = self.validate_syntax(node)
        return is_valid 