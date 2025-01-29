"""Tree-sitter query service for pattern matching."""
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from tree_sitter import Query, Node, Tree, QueryError, Language, Point

from tree_sitter_language_pack import get_binding, get_language, get_parser

from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.utils.logging import get_logger, LoggerFactory
from GithubAnalyzer.utils.logging.tree_sitter_logging import TreeSitterLogHandler

from .utils import (
    get_node_text,
    node_to_dict,
    iter_children,
    get_node_hierarchy,
    find_common_ancestor,
    LanguageId,
    QueryPattern,
    NodeDict,
    NodeList,
    QueryResult,
    is_valid_node,
    get_node_type,
    get_node_text_safe,
    TreeSitterServiceBase
)
from .query_patterns import (
    get_query_pattern,
    get_optimization_settings,
    QueryOptimizationSettings,
    QUERY_PATTERNS
)
from .language_service import LanguageService
from .traversal_service import TreeSitterTraversal

logger = get_logger(__name__)

@dataclass
class TreeSitterQueryHandler(TreeSitterServiceBase):
    """Handler for tree-sitter queries."""
    
    language: Optional[Language] = None
    language_name: str = "python"
    
    def __post_init__(self):
        """Initialize query handler.
        
        Args:
            language: Tree-sitter Language object to use for queries
            language_name: Name of the language (e.g. "python", "javascript")
        """
        super().__post_init__()
        self._traversal = TreeSitterTraversal()
        self._language_name = self.language_name
        self._language_service = LanguageService()
        
        # Initialize language - either use provided Language object or get from service
        self._language = self.language if self.language else self._language_service.get_language_object(self.language_name)
            
        if not self._language:
            raise ValueError(f"Could not get language for {self.language_name}")
        
        # Initialize query components
        self._pattern_queries = {}
        self._disabled_patterns = set()
        self._disabled_captures = set()
        self._function_pattern = get_query_pattern(self._language_name, "function")
        self._class_pattern = get_query_pattern(self._language_name, "class")
        
        # Initialize performance metrics
        self._operation_times = {}
        
        # Log initialization
        self._logger.debug("TreeSitterQueryHandler initialized", extra={
            'component': 'tree_sitter.query',
            'thread_id': threading.get_ident(),
            'language': self._language_name,
            'patterns': list(QUERY_PATTERNS.get(self._language_name, {}).keys())
        })

    def create_query(self, query_string: str, language: Optional[str] = None) -> Query:
        """Create an optimized tree-sitter query.
        
        Args:
            query_string: Query pattern string
            language: Optional language identifier (uses default if not specified)
            
        Returns:
            Configured Query object
            
        Raises:
            QueryError: If query creation fails
        """
        start_time = self._time_operation('create_query')
        
        try:
            # Get language from service
            lang = language or self._language_name
            lang_obj = self._language_service.get_language_object(lang)
            if not lang_obj:
                raise QueryError(f"Could not get language object for {lang}")
            
            query = Query(lang_obj, query_string)
            
            # Check query validity
            for i in range(query.pattern_count):
                if not query.is_pattern_rooted(i):
                    self._logger.warning(f"Pattern {i} is not rooted")
                    
            return query
            
        except Exception as e:
            raise QueryError(f"Failed to create query: {e}")
            
        finally:
            self._end_operation('create_query', start_time)

    def execute_query(self, query: Query, node: Union[Node, Tree]) -> Dict[str, List[Node]]:
        """Execute a query with native tree-sitter optimizations.
        
        Args:
            query: Query to execute
            node: Node or Tree to execute query on
            
        Returns:
            Dictionary mapping capture names to lists of captured nodes
            
        Raises:
            QueryError: If query execution fails
        """
        start_time = self._time_operation('execute_query')
        
        try:
            target_node = node.root_node if isinstance(node, Tree) else node
            
            # Get query stats before execution
            stats = self.get_query_stats(query)
            self._logger.debug({
                "message": "Executing query",
                "context": {
                    "stats": stats,
                    "node_type": target_node.type
                }
            })
            
            # Execute query and get all captures
            captures = defaultdict(list)
            for pattern_idx, match in query.matches(target_node):
                if pattern_idx not in self._disabled_patterns:
                    # Add captures from match
                    for name, nodes in match.items():
                        if name not in self._disabled_captures:
                            captures[name].extend(nodes)
            
            # Check execution status
            if query.did_exceed_match_limit:
                self._logger.warning("Query exceeded match limit")
                
            return dict(captures)
            
        except Exception as e:
            raise QueryError(f"Query execution failed: {e}")
            
        finally:
            self._end_operation('execute_query', start_time)

    def _time_operation(self, operation: str) -> float:
        """Start timing an operation."""
        return time.time()

    def _end_operation(self, operation: str, start_time: float):
        """End timing an operation and store result."""
        duration = time.time() - start_time
        self._operation_times[operation] = duration

    def get_query_stats(self, query: Query) -> Dict[str, Any]:
        """Get statistics about a query."""
        return {
            'pattern_count': query.pattern_count,
            'capture_names': query.capture_names()
        }

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

    def find_nodes(self, tree: Tree, pattern_type: str, language: Optional[str] = None) -> List[Dict[str, Node]]:
        """Find nodes using native tree-sitter query methods.
        
        Args:
            tree: The tree to search
            pattern_type: Type of pattern to match
            language: Optional language identifier
            
        Returns:
            List of dictionaries containing captured nodes
        """
        try:
            # Get pattern for language
            lang = language or self._language_name
            pattern = get_query_pattern(lang, pattern_type)
            if not pattern:
                return []
                
            # Create and execute query
            query = self.create_query(pattern, lang)
            if not query:
                return []
                
            # Use native matches() method
            matches = []
            for pattern_idx, match in query.matches(tree.root_node):
                # Verify pattern is valid
                if (query.is_pattern_rooted(pattern_idx) and
                    pattern_idx not in self._disabled_patterns):
                    # Convert capture names from bytes to str
                    capture_dict = {}
                    for name, node in match.items():
                        name_str = name.decode('utf-8') if isinstance(name, bytes) else str(name)
                        capture_dict[name_str] = node
                    matches.append(capture_dict)
                    
            return matches
        except Exception as e:
            self._logger.error(f"Error finding nodes: {str(e)}")
            return []

    def validate_node(self, node: Node) -> Tuple[bool, List[str]]:
        """Validate node using native tree-sitter methods.
        
        Args:
            node: Node to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check node state
        if node.has_error:
            # Get valid symbols that could appear
            valid_symbols = self.get_valid_symbols_at_error(node)
            errors.append(
                f"Syntax error at {node.start_point}. "
                f"Expected one of: {', '.join(valid_symbols)}"
            )
            
        # Check pattern validity
        query = self._get_pattern_query(node.type)
        if query:
            for i in range(query.pattern_count):
                if not query.is_pattern_guaranteed_at_step(i):
                    errors.append(
                        f"Node {node.type} is not guaranteed at "
                        f"position {node.start_point}"
                    )
                    
        return len(errors) == 0, errors

    def get_valid_symbols_at_error(self, node: Node, language: Optional[str] = None) -> List[str]:
        """Get valid symbols that could appear at an error node.
        
        Uses Tree-sitter's LookaheadIterator to find valid symbols.
        
        Args:
            node: The error node to analyze
            language: Optional language identifier
            
        Returns:
            List of valid symbol names
        """
        if not node or not node.has_error:
            return []
            
        lang = language or self._language.name
        lang_obj = get_language(lang)
        if not lang_obj:
            return []
            
        try:
            # Get first leaf node state
            cursor = node.walk()
            while cursor.goto_first_child():
                pass
                
            # Create lookahead iterator
            lookahead = lang_obj.lookahead_iterator(
                cursor.node.parse_state
            )
            
            # Get all valid symbol names
            return list(lookahead.iter_names())
            
        except Exception as e:
            self._logger.error(f"Error getting valid symbols: {e}")
            return []

    def configure_query(self, query: Query, settings: QueryOptimizationSettings):
        """Configure query with optimization settings."""
        if settings.match_limit:
            query.set_match_limit(settings.match_limit)
            
        if settings.timeout_micros:
            query.set_timeout_micros(settings.timeout_micros)
            
        if settings.byte_range:
            query.set_byte_range(settings.byte_range)
            
        if settings.point_range:
            query.set_point_range(settings.point_range)

    def get_matches(self, query: Query, node: Union[Node, Tree]) -> List[Dict[str, Node]]:
        """Get matches from a query execution using native tree-sitter matches.
        
        Args:
            query: Query to execute
            node: Node or Tree to execute query on
            
        Returns:
            List of match dictionaries
        """
        start_time = self._time_operation('get_matches')
        
        try:
            target_node = node.root_node if isinstance(node, Tree) else node
            
            # Get matches using native method
            matches = []
            for pattern_idx, match in query.matches(target_node):
                if pattern_idx not in self._disabled_patterns:
                    # Check pattern validity
                    if query.is_pattern_rooted(pattern_idx):
                        matches.append(match)
                        
            return matches
            
        except Exception as e:
            self._logger.error(f"Failed to get matches: {e}")
            return []
            
        finally:
            self._end_operation('get_matches', start_time)

    def get_pattern_info(self, query: Query, pattern_index: int) -> Dict[str, Any]:
        """Get information about a query pattern."""
        start_time = self._time_operation('get_pattern_info')
        
        try:
            return {
                "is_rooted": query.is_pattern_rooted(pattern_index),
                "is_non_local": query.is_pattern_non_local(pattern_index),
                "assertions": query.pattern_assertions(pattern_index),
                "settings": query.pattern_settings(pattern_index)
            }
        finally:
            self._end_operation('get_pattern_info', start_time)

    def _get_pattern_query(self, pattern_type: str, language: Optional[str] = None) -> Optional[Query]:
        """Get cached query for pattern type.

        Args:
            pattern_type: Type of pattern to get query for
            language: Optional language identifier

        Returns:
            Cached query or None if not found
        """
        lang = language or self._language.name
        return self._pattern_queries.get(lang, {}).get(pattern_type)

    def _process_captures(self, captures: Dict[str, List[Node]]) -> Dict[str, List[Node]]:
        """Process captures into a dictionary mapping capture names to node lists.

        Args:
            captures: Dictionary mapping capture names to lists of nodes from tree-sitter

        Returns:
            Dictionary mapping capture names to lists of nodes
        """
        return captures  # Tree-sitter already returns the format we want

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

    def validate_syntax(self, node: Node, language: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Validate syntax using error patterns.
        
        Args:
            node: Node to validate
            language: Optional language identifier
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Find error nodes
        error_matches = self.find_nodes(node, "error", language)
        for match in error_matches:
            if 'error.syntax' in match:
                errors.append(f"Syntax error at {match['error.syntax'].start_point}")
            if 'error.missing' in match:
                errors.append(f"Missing node at {match['error.missing'].start_point}")
                
        return len(errors) == 0, errors

    def find_functions(self, node: Union[Node, Tree], language: Optional[str] = None) -> List[Dict[str, Node]]:
        """Find function nodes in a tree.
        
        Args:
            node: Node or Tree to search
            language: Optional language identifier
            
        Returns:
            List of dictionaries containing function nodes
        """
        return self.find_nodes(node, "function", language)

    def find_classes(self, node: Node, language: Optional[str] = None) -> List[Dict[str, Node]]:
        """Find class definitions with their components.
        
        Args:
            node: Root node to search in
            language: Optional language identifier
            
        Returns:
            List of dictionaries containing class components
        """
        return self.find_nodes(node, "class", language)

    def find_nodes_by_type(self, node: Node, node_type: str, language: Optional[str] = None) -> List[Node]:
        """Find nodes of a specific type using native tree-sitter query.
        
        Args:
            node: Root node to search in
            node_type: Type of nodes to find
            language: Optional language identifier
            
        Returns:
            List of matching nodes
        """
        lang = language or self._language.name
        lang_obj = get_language(lang)
        if not lang_obj:
            return []
            
        # Create query pattern with target capture
        pattern = f"""
            ({node_type}) @target
            (#is-not? @target error)
            (#is-not? @target missing)
        """
        
        try:
            query = self.create_query(pattern, lang)
            if not query:
                return []
                
            # Get matches and extract target nodes
            matches = []
            for pattern_idx, match in query.matches(node):
                if 'target' in match:
                    matches.append(match['target'])
                    
            return matches
            
        except Exception as e:
            self._logger.error(f"Failed to find nodes by type: {e}")
            return []

    def is_valid_node(self, node: Node, language: Optional[str] = None) -> bool:
        """Check if a node is valid using native tree-sitter validation.
        
        Args:
            node: Node to validate
            language: Optional language identifier
            
        Returns:
            True if node is valid
        """
        if not node:
            return False
            
        # Check basic node validity
        if node.has_error or node.is_missing:
            return False
            
        lang = language or self._language.name
        lang_obj = get_language(lang)
        if not lang_obj:
            return False
            
        # Get node type pattern
        pattern = f"""
            ({node.type}) @node
            (#is? @node complete)
            (#is-not? @node error)
            (#is-not? @node missing)
        """
        
        try:
            query = self.create_query(pattern, lang)
            if not query:
                return False
                
            # Check if node matches validity pattern
            matches = query.matches(node)
            return len(matches) > 0
            
        except Exception as e:
            self._logger.error(f"Error validating node: {e}")
            return False

    def get_query_pattern(self, pattern_type: str, language: Optional[str] = None) -> str:
        """Get a query pattern for a specific language and pattern type.
        
        Args:
            pattern_type: Type of pattern to get
            language: Optional language identifier (uses default if not specified)
            
        Returns:
            Query pattern string
            
        Raises:
            KeyError: If language or pattern type not found
        """
        lang = language or self._language.name
        pattern_lang = self._language_service.get_language_map().get(lang, lang)
        return get_query_pattern(pattern_lang, pattern_type)