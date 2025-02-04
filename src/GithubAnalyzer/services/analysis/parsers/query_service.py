"""Tree-sitter query service for pattern matching."""
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from tree_sitter import Query, Node, Tree, QueryError, Language, Point, Parser
import logging

from tree_sitter_language_pack import get_binding, get_language, get_parser

from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.utils.logging import get_logger, get_tree_sitter_logger

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

# Initialize logger with proper configuration
logger = get_logger(__name__)

@dataclass
class TreeSitterQueryHandler(TreeSitterServiceBase):
    """Handler for tree-sitter queries."""
    
    language: Optional[Language] = None
    language_name: str = "python"
    
    def __post_init__(self):
        """Initialize query handler."""
        super().__post_init__()
        self._logger = logger
        self._start_time = time.time()
        
        self._logger.debug("QueryHandler initialized", extra={
            'context': {
                'module': 'query',
                'thread': threading.get_ident(),
                'duration_ms': 0
            }
        })
        
        # Initialize services
        self._language_service = LanguageService()
        self._traversal = TreeSitterTraversal()
        
        self._language_name = self.language_name
        
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
        
        # Set up logger callback
        def logger_callback(log_type: int, msg: str) -> None:
            level = logging.ERROR if log_type == 1 else logging.DEBUG
            self._logger.log(level, msg, extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'error' if log_type == 1 else 'parse'
                }
            })
            
        # Set logger on language service parser
        parser = self._language_service.get_parser(self._language_name)
        if parser:
            parser.logger = logger_callback

    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """Get standard context for logging.
        
        Args:
            **kwargs: Additional context key-value pairs
            
        Returns:
            Dict with standard context fields plus any additional fields
        """
        context = {
            'module': 'query',
            'thread': threading.get_ident(),
            'duration_ms': (time.time() - self._start_time) * 1000
        }
        context.update(kwargs)
        return context

    def _log(self, level: str, message: str, **kwargs) -> None:
        """Log with consistent context.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Message to log
            **kwargs: Additional context key-value pairs
        """
        context = self._get_context(**kwargs)
        getattr(self._logger, level)(message, extra={'context': context})

    def create_query(self, query_string: str, language_name: Optional[str] = None) -> Query:
        """Create an optimized tree-sitter query.
        
        Args:
            query_string: Query string to parse
            language_name: Optional language name override
            
        Returns:
            Optimized Query object
            
        Raises:
            QueryError: If query creation fails
        """
        start_time = self._time_operation('create_query')
        
        try:
            # Get language
            lang = self._language_service.get_language_object(language_name or self._language_name)
            if not lang:
                raise ValueError(f"Could not get language for {language_name or self._language_name}")
            
            # Create and optimize query
            query = lang.query(query_string)
            
            # Log optimization info using tree-sitter logger
            self._log("debug", "Query created and optimized", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'optimization',
                    'language': language_name or self._language_name,
                    'pattern_count': query.pattern_count,
                    'capture_count': query.capture_count,
                    'match_limit': query.match_limit,
                    'query_string': query_string
                }
            })
            
            # Check for unrooted patterns
            for pattern_index in range(query.pattern_count):
                if not query.is_pattern_rooted(pattern_index):
                    self._log("warning", f"Pattern {pattern_index} is not rooted", extra={
                        'context': {
                            'source': 'tree-sitter',
                            'type': 'query',
                            'log_type': 'validation',
                            'pattern_index': pattern_index
                        }
                    })
            
            return query
            
        except Exception as e:
            self._log("error", f"Failed to create query: {str(e)}", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'error',
                    'error': str(e),
                    'query_string': query_string
                }
            })
            raise
            
        finally:
            # Log timing
            duration = (time.time() - start_time) * 1000
            self._log("debug", "Query creation completed", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'timing',
                    'operation': 'create_query',
                    'duration_ms': duration
                }
            })

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
            self._log("debug", "Executing query", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'execution',
                    'stats': stats,
                    'node_type': target_node.type,
                    'node_start_point': target_node.start_point,
                    'node_end_point': target_node.end_point
                }
            })
            
            # Execute query and get captures
            captures = query.captures(target_node)
            
            # Log each capture
            for name, nodes in captures.items():
                for node in nodes:
                    self._log("debug", f"Query captured node", extra={
                        'context': {
                            'source': 'tree-sitter',
                            'type': 'query',
                            'log_type': 'capture',
                            'capture_name': name,
                            'node_type': node.type,
                            'node_text': get_node_text_safe(node),
                            'node_start_point': node.start_point,
                            'node_end_point': node.end_point
                        }
                    })
            
            return captures
            
        except Exception as e:
            self._log("error", f"Failed to execute query: {e}", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'error',
                    'error': str(e),
                    'node_type': target_node.type if target_node else None
                }
            })
            raise QueryError(f"Failed to execute query: {e}")
            
        finally:
            duration = self._end_operation('execute_query', start_time)
            self._log("debug", "Query execution completed", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'timing',
                    'operation': 'execute_query',
                    'duration_ms': duration * 1000,
                    'capture_count': len(captures) if 'captures' in locals() else 0
                }
            })

    def _time_operation(self, operation: str) -> float:
        """Start timing an operation."""
        return time.time()

    def _end_operation(self, operation: str, start_time: float):
        """End timing an operation and store result."""
        duration = time.time() - start_time
        self._operation_times[operation] = duration
        return duration

    def get_query_stats(self, query: Query) -> Dict[str, Any]:
        """Get statistics about a query."""
        return {
            'pattern_count': query.pattern_count,
            'capture_count': query.capture_count,
            'match_limit': query.match_limit,
            'did_exceed_match_limit': query.did_exceed_match_limit
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

    def find_nodes(self, tree_or_node: Union[Tree, Node], pattern_type: str, language: Optional[str] = None) -> List[Dict[str, Node]]:
        """Find nodes using native tree-sitter query methods.
        
        Args:
            tree_or_node: The tree or node to search
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
                
            # Get target node
            target_node = tree_or_node.root_node if isinstance(tree_or_node, Tree) else tree_or_node
                
            # Use native matches() method
            matches = []
            for pattern_idx, match in query.matches(target_node):
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
            self._log("error", f"Error finding nodes: {str(e)}")
            return []

    def validate_node(self, node: Node, language: Optional[str] = None) -> Tuple[bool, List[str]]:
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
            self._log("error", f"Error getting valid symbols: {e}")
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
            self._log("error", f"Failed to get matches: {e}")
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

    def find_functions(self, target_node: Union[Node, Tree]) -> List[Dict[str, Any]]:
        """Find all function definitions in the given node.
        
        Args:
            target_node: Node or Tree to search for functions
            
        Returns:
            List of function information dictionaries
        """
        pattern = self._function_pattern
        
        try:
            # Create and execute query
            query = self._language.query(pattern)
            captures_dict = query.captures(target_node)

            # Log detailed capture information
            self._log("debug", "Found function captures", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'capture_names': list(captures_dict.keys()),
                    'capture_counts': {name: len(nodes) for name, nodes in captures_dict.items()},
                    'language': self._language_name
                }
            })

            # Group captures by function definition node
            functions = []
            seen_funcs = set()

            # First process function definitions
            for func_node in captures_dict.get('function.def', []):
                if func_node in seen_funcs:
                    continue
                    
                seen_funcs.add(func_node)
                func_info = {
                    'function.def': func_node,
                    'function.name': None,
                    'name': None,
                    'is_named': False,
                    'start_point': func_node.start_point,
                    'end_point': func_node.end_point,
                    'type': func_node.type
                }
                
                # Log function definition found
                self._log("debug", f"Found function definition", extra={
                    'context': {
                        'source': 'tree-sitter',
                        'type': 'query',
                        'function_type': func_node.type,
                        'start_point': func_node.start_point,
                        'end_point': func_node.end_point
                    }
                })
                
                functions.append(func_info)

            # Then process function names
            for name_node in captures_dict.get('function.name', []):
                # Find the function this name belongs to by checking parent nodes
                parent = name_node.parent
                while parent:
                    if parent in seen_funcs:
                        # Find the function entry and update it
                        for func in functions:
                            if func['function.def'] == parent:
                                func['function.name'] = name_node
                                func['name'] = name_node.text.decode('utf8')
                                func['is_named'] = True
                                
                                # Log function name association
                                self._log("debug", f"Associated function name", extra={
                                    'context': {
                                        'source': 'tree-sitter',
                                        'type': 'query',
                                        'function_name': func['name'],
                                        'function_type': func['type']
                                    }
                                })
                                break
                        break
                    parent = parent.parent

            self._log("info", "Function search complete", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'total_functions': len(functions),
                    'named_functions': sum(1 for f in functions if f['is_named']),
                    'language': self._language_name
                }
            })

            return functions
            
        except Exception as e:
            self._log("error", f"Error finding functions: {str(e)}", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            })
            return []

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
            self._log("error", f"Failed to find nodes by type: {e}")
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
            self._log("error", f"Error validating node: {e}")
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
        pattern_lang = self._language_service.extension_to_language.get(lang, lang)
        return get_query_pattern(pattern_lang, pattern_type)

    def get_pattern_for_language(self, pattern_type: str, language: Optional[str] = None) -> Optional[str]:
        """Get a query pattern for a specific language.
        
        Args:
            pattern_type: The type of pattern to retrieve
            language: Optional language override. If not provided, uses the current language.
            
        Returns:
            Query pattern string or None if not found
        """
        try:
            if not language:
                language = self._language_name
            
            pattern = self.get_query_pattern(pattern_type, language)
            if not pattern:
                self._logger.warning(f"No pattern found for {pattern_type} in {language}")
                return None
                
            return pattern
        except Exception as e:
            self._logger.error(f"Error getting pattern for {pattern_type} in {language}: {str(e)}")
            return None

def find_functions(tree: Tree, query: Query) -> List[Dict[str, Any]]:
    """Find all functions in the tree using the provided query.
    
    Args:
        tree: The parsed tree to search
        query: The compiled query to use
        
    Returns:
        List of found functions with their details
    """
    functions = []
    
    try:
        # Execute query using captures() method
        captures = query.captures(tree.root_node)
        
        logger.debug(
            "Executing function query",
            extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'query',
                    'captures_count': len(captures)
                }
            }
        )
        
        # Group captures by their function definition
        current_function = {}
        
        for capture_name, node in captures:
            try:
                if capture_name == 'function.def':
                    # If we have a previous function, add it to the list
                    if current_function:
                        functions.append(current_function)
                    
                    # Start a new function
                    current_function = {
                        'type': node.type,
                        'start_point': node.start_point,
                        'end_point': node.end_point,
                        'name': None,
                        'params': None,
                        'body': None
                    }
                    
                elif capture_name == 'function.name' and current_function:
                    current_function['name'] = node.text.decode('utf-8')
                elif capture_name == 'function.params' and current_function:
                    current_function['params'] = node.text.decode('utf-8')
                elif capture_name == 'function.body' and current_function:
                    current_function['body'] = node.text.decode('utf-8')
                
                logger.debug(
                    f"Processing capture {capture_name}",
                    extra={
                        'context': {
                            'source': 'tree-sitter',
                            'type': 'query',
                            'log_type': 'query',
                            'capture_name': capture_name,
                            'node_type': node.type,
                            'start_point': node.start_point,
                            'end_point': node.end_point
                        }
                    }
                )
                
            except Exception as e:
                logger.error(
                    f"Error processing capture {capture_name}: {str(e)}",
                    extra={
                        'context': {
                            'source': 'tree-sitter',
                            'type': 'query',
                            'log_type': 'error',
                            'error_type': type(e).__name__,
                            'capture_name': capture_name
                        }
                    }
                )
                continue
        
        # Add the last function if exists
        if current_function:
            functions.append(current_function)
            
    except Exception as e:
        logger.error(
            f"Error executing function query: {str(e)}",
            extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'error',
                    'error_type': type(e).__name__
                }
            }
        )
        raise
        
    return functions