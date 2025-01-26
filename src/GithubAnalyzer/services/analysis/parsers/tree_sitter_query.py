from tree_sitter import Query, Node, Tree, QueryError, Language, Point
from tree_sitter_language_pack import get_binding, get_language, get_parser
import logging

from ....utils.logging.tree_sitter_logging import TreeSitterLogHandler
"""Tree-sitter query handler."""
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from .query_patterns import (
    get_query_pattern,
    get_optimization_settings,
    QueryOptimizationSettings,
    QUERY_PATTERNS
)
from .tree_sitter_traversal import TreeSitterTraversal
from collections import defaultdict

# Cache language at module level
_PYTHON_LANGUAGE = None

def get_cached_language():
    global _PYTHON_LANGUAGE
    if _PYTHON_LANGUAGE is None:
        python_binding = get_binding('python')
        _PYTHON_LANGUAGE = Language(python_binding)
    return _PYTHON_LANGUAGE

class TreeSitterQueryHandler:
    """Handles tree-sitter query operations."""
    
    def __init__(self, logger: Optional[TreeSitterLogHandler] = None):
        """Initialize TreeSitterQueryHandler.

        Args:
            logger: Optional logger for structured logging
        """
        self._traversal = TreeSitterTraversal()
        self._pattern_queries = {}
        self._disabled_captures = set()
        self._disabled_patterns = set()
        
        # Use cached language
        self._language = get_cached_language()
        self._logger = logger
        
        if self._logger:
            self._logger.debug({
                "message": "Initializing TreeSitterQueryHandler",
                "context": {
                    "language": "python",
                    "patterns": list(QUERY_PATTERNS["python"].keys())
                }
            })

        # Initialize pattern queries
        for pattern_type in QUERY_PATTERNS["python"]:
            pattern = get_query_pattern("python", pattern_type)
            try:
                self._pattern_queries[pattern_type] = self.create_query(pattern)
                if self._logger:
                    self._logger.debug({
                        "message": f"Created query for pattern {pattern_type}",
                        "context": {"pattern": pattern}
                    })
            except Exception as e:
                if self._logger:
                    self._logger.error({
                        "message": f"Failed to create query for pattern {pattern_type}",
                        "context": {
                            "error": str(e),
                            "pattern": pattern
                        }
                    })

    def create_query(self, language_or_query: Union[Language, str], query_string: Optional[str] = None) -> Query:
        """Create a tree-sitter query from a string.
        
        This method can be called in two ways:
        1. create_query(language, query_string)
        2. create_query(query_string)
        
        Args:
            language_or_query: Either a Language object or a query string
            query_string: The query string if language is provided, otherwise None
            
        Returns:
            Query: The created query
            
        Raises:
            QueryError: If the query cannot be created
        """
        details = {
            "language": str(language_or_query) if isinstance(language_or_query, Language) else "default",
            "query_string": query_string or language_or_query
        }
        
        try:
            if isinstance(language_or_query, Language):
                if query_string is None:
                    self._logger.error({
                        "message": "Query string must be provided when language is provided",
                        "context": details
                    })
                    raise ValueError("query_string must be provided when language is provided")
                return Query(language_or_query, query_string)
            else:
                # If only query string provided, use default language
                return Query(self._language, language_or_query)
        except Exception as e:
            error_details = {**details, "error": str(e)}
            if self._logger:
                self._logger.error({
                    "message": "Failed to create query",
                    "context": error_details
                })
            raise QueryError(
                message=f"Failed to create query: {e}",
                details=str(error_details)
            )

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
            if self._logger:
                self._logger.error(f"Failed to get query stats: {str(e)}")
            raise QueryError(str(e))

    def execute_query(self, query: Query, node: Union[Node, Tree]) -> Dict[str, List[Node]]:
        """Execute a query on a node or tree.
        
        Args:
            query: Query to execute
            node: Node or Tree to execute query on
            
        Returns:
            Dictionary mapping capture names to lists of captured nodes
            
        Raises:
            QueryError: If query execution failed
        """
        details = {
            "query_stats": self.get_query_stats(query),
            "node_type": node.root_node.type if isinstance(node, Tree) else node.type,
            "disabled_captures": list(self._disabled_captures),
            "disabled_patterns": list(self._disabled_patterns)
        }
        
        try:
            # Get the node to query
            target_node = node.root_node if isinstance(node, Tree) else node
            
            self._logger.debug({
                "message": "Executing query",
                "context": details
            })
            
            # Get captures directly as a dictionary
            captures = query.captures(target_node)
            
            # Filter out disabled captures
            results = {
                name: nodes 
                for name, nodes in captures.items()
                if name not in self._disabled_captures
            }
            
            return results
            
        except Exception as e:
            error_details = {**details, "error": str(e)}
            self._logger.error({
                "message": "Failed to execute query",
                "context": error_details
            })
            raise QueryError(
                message=f"Failed to execute query: {e}",
                details=str(error_details)
            )

    def get_matches(self, query: Query, node: Union[Node, Tree]) -> List[Dict[str, List[Node]]]:
        """Get matches from a query execution.
        
        Args:
            query: Query to execute
            node: Node or Tree to execute query on
            
        Returns:
            List of match dictionaries
        """
        try:
            target_node = node.root_node if isinstance(node, Tree) else node
            matches = query.matches(target_node)
            return [
                match for pattern_idx, match in matches
                if pattern_idx not in self._disabled_patterns
            ]
        except Exception as e:
            self._logger.error(f"Failed to get matches: {e}", exc_info=True)
            raise

    def configure_query(self, query: Query, settings: QueryOptimizationSettings):
        """Configure query with optimization settings."""
        try:
            if settings.match_limit:
                query.match_limit = settings.match_limit
            if settings.timeout_micros:
                query.timeout_micros = settings.timeout_micros
        except Exception as e:
            if self._logger:
                self._logger.warning(f"Query configuration settings are no longer supported: {str(e)}")

    def get_pattern_info(self, query: Query, pattern_index: int) -> Dict[str, Any]:
        """Get information about a query pattern."""
        return {
            "is_rooted": query.is_pattern_rooted(pattern_index),
            "is_non_local": query.is_pattern_non_local(pattern_index),
            "assertions": query.pattern_assertions(pattern_index),
            "settings": query.pattern_settings(pattern_index)
        }

    def _get_pattern_query(self, pattern_type: str) -> Optional[Query]:
        """Get cached query for pattern type.

        Args:
            pattern_type: Type of pattern to get query for

        Returns:
            Cached query or None if not found
        """
        return self._pattern_queries.get(pattern_type)

    def _process_captures(self, captures: Dict[str, List[Node]]) -> Dict[str, List[Node]]:
        """Process captures into a dictionary mapping capture names to node lists.

        Args:
            captures: Dictionary mapping capture names to lists of nodes from tree-sitter

        Returns:
            Dictionary mapping capture names to lists of nodes
        """
        return captures  # Tree-sitter already returns the format we want

    def find_nodes(self, tree: Tree, pattern_type: str) -> List[Node]:
        """Find nodes matching a pattern type.

        Args:
            tree: The tree to search
            pattern_type: The type of pattern to match

        Returns:
            List[Node]: The matching nodes

        Raises:
            QueryError: If the pattern type is invalid
        """
        query = self._get_pattern_query(pattern_type)
        if not query:
            # Create the query if it doesn't exist
            pattern = get_query_pattern("python", pattern_type)
            if not pattern:
                return []
            query = self.create_query(pattern)
            self._pattern_queries[pattern_type] = query

        # Always use the root node for searching
        captures = self.execute_query(query, tree.root_node)
        
        # Return nodes for the pattern type if any were captured
        return captures.get(pattern_type, [])

    def find_missing_nodes(self, node: Node) -> List[Node]:
        """Find missing nodes using TreeSitterTraversal.
        
        Args:
            node: The node to search
            
        Returns:
            List[Node]: List of missing nodes
        """
        return self._traversal.find_missing_nodes(node)

    def find_error_nodes(self, node: Node) -> List[Node]:
        """Find error nodes using TreeSitterTraversal.
        
        Args:
            node: The node to search
            
        Returns:
            List[Node]: List of error nodes
        """
        return self._traversal.find_error_nodes(node)

    def validate_syntax(self, node: Node) -> Tuple[bool, List[str]]:
        """Validate syntax using error and missing node queries.
        
        Args:
            node: Node to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Check for error nodes
        error_nodes = self._traversal.find_error_nodes(node)
        for error_node in error_nodes:
            errors.append(f"Syntax error at line {error_node.start_point[0] + 1}, column {error_node.start_point[1]}")
                
        # Check for missing nodes
        missing_nodes = self._traversal.find_missing_nodes(node)
        for missing_node in missing_nodes:
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
        query = self.create_query(get_language('python'), self._FUNCTION_PATTERN)
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
            if self._logger:
                self._logger.error(f"Failed to find functions: {str(e)}")
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
        query = self.create_query(get_language('python'), self._CLASS_PATTERN)
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
            if self._logger:
                self._logger.error(f"Failed to find classes: {str(e)}")
            return []

    def find_nodes_by_type(self, node: Node, node_type: str) -> List[Node]:
        """Find nodes of a specific type using query pattern."""
        pattern = f"({node_type}) @target"
        query = self.create_query(get_language('python'), pattern)
        if not query:
            return []
            
        return [capture[0] for capture in query.captures(node)]

    def is_valid_node(self, node: Node) -> bool:
        """Check if a node is valid (no errors or missing parts)."""
        if not node:
            return False
            
        is_valid, _ = self.validate_syntax(node)
        return is_valid