"""Core tree-sitter query handler functionality."""
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from tree_sitter import Language, Node, Parser, Point, Query, QueryError, Tree
from tree_sitter_language_pack import get_binding, get_language, get_parser

from GithubAnalyzer.models.analysis.query import (QueryCapture, QueryExecutor,
                                                  QueryOptimizationSettings,
                                                  QueryPattern, QueryResult,
                                                  QueryStats)
from GithubAnalyzer.models.analysis.types import LanguageId
from GithubAnalyzer.models.core.ast import NodeDict, NodeList
from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.models.core.traversal import TreeSitterTraversal
from GithubAnalyzer.models.core.tree_sitter_core import (
    get_node_text, get_node_type, get_node_range, is_valid_node,
    node_to_dict, iter_children
)
from GithubAnalyzer.services.parsers.core.base_parser_service import \
    BaseParserService
from GithubAnalyzer.services.parsers.core.language_service import \
    LanguageService
from GithubAnalyzer.utils.logging import get_logger
from GithubAnalyzer.utils.timing import timer

# Initialize logger
logger = get_logger(__name__)

@dataclass
class TreeSitterQueryHandler(BaseParserService):
    """Handler for tree-sitter queries with enhanced language support."""
    
    language_name: str = "csharp"
    _language_service: LanguageService = field(default_factory=LanguageService)
    _executor: QueryExecutor = field(default_factory=QueryExecutor)
    _traversal: TreeSitterTraversal = field(default_factory=TreeSitterTraversal)
    _start_time: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Initialize query handler."""
        super().__post_init__()
        
        self._log("debug", "QueryHandler initialized",
                module='query',
                thread=threading.get_ident(),
                duration_ms=0)
        
        # Initialize language
        self._language_name = self.language_name
        self.language = self._language_service.get_tree_sitter_language(self.language_name)
        if not self.language:
            raise ValueError(f"Could not get language for {self.language_name}")
        
        # Initialize query components
        self._pattern_queries = {}
        self._disabled_patterns = set()
        self._disabled_captures = set()
        
        # Initialize performance metrics
        self._operation_times = {}
        
        # Set up logger callback
        def logger_callback(log_type: int, msg: str) -> None:
            level = logging.ERROR if log_type == 1 else logging.DEBUG
            self._log(level, msg,
                    source='tree-sitter',
                    type='query',
                    log_type='error' if log_type == 1 else 'parse')
            
        # Set logger on language service parser
        parser = self._language_service.get_parser(self._language_name)
        if parser:
            parser.logger = logger_callback

    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """Get standard context for logging."""
        context = {
            'module': 'query',
            'thread': threading.get_ident(),
            'duration_ms': (time.time() - self._start_time) * 1000
        }
        context.update(kwargs)
        return context

    def _log(self, level: str, message: str, **kwargs) -> None:
        """Log with consistent context."""
        context = self._get_context(**kwargs)
        getattr(self._logger, level)(message, extra={'context': context})

    def create_query(self, query_string: str, language_name: Optional[str] = None) -> Query:
        """Create an optimized tree-sitter query."""
        start_time = self._time_operation('create_query')
        
        try:
            # Get language
            lang = self._language_service.get_language_object(language_name or self._language_name)
            if not lang:
                raise ValueError(f"Could not get language for {language_name or self._language_name}")
            
            # Create and optimize query
            query = lang.query(query_string)
            
            # Create query stats
            stats = QueryStats(
                pattern_count=query.pattern_count,
                capture_count=query.capture_count,
                match_limit=query.match_limit
            )
            
            # Check for unrooted patterns
            for pattern_index in range(query.pattern_count):
                if not query.is_pattern_rooted(pattern_index):
                    stats.unrooted_patterns.append(pattern_index)
                    self._log("warning", f"Pattern {pattern_index} is not rooted", extra={
                        'context': {
                            'source': 'tree-sitter',
                            'type': 'query',
                            'log_type': 'validation',
                            'pattern_index': pattern_index
                        }
                    })
            
            # Log optimization info using tree-sitter logger
            self._log("debug", "Query created and optimized", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'optimization',
                    'language': language_name or self._language_name,
                    'stats': stats.__dict__,
                    'query_string': query_string
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

    def execute_query(self, query: Query, node: Union[Node, Tree]) -> QueryResult:
        """Execute a query with native tree-sitter optimizations."""
        start_time = self._time_operation('execute_query')
        
        try:
            target_node = node.root_node if isinstance(node, Tree) else node
            if not target_node:
                raise QueryError("Invalid target node")
            
            # Get query stats before execution
            stats = QueryStats(
                pattern_count=query.pattern_count,
                capture_count=query.capture_count,
                match_limit=query.match_limit
            )
            
            # Check for syntax errors
            has_errors = False
            if hasattr(target_node, 'has_error'):
                has_errors = target_node.has_error
            elif hasattr(target_node, 'isErr'):
                has_errors = target_node.isErr

            if has_errors:
                self._log("warning", "Node contains syntax errors", extra={
                    'context': {
                        'source': 'tree-sitter',
                        'type': 'query',
                        'log_type': 'validation',
                        'node_type': target_node.type if hasattr(target_node, 'type') else None,
                        'has_error': has_errors
                    }
                })
            
            self._log("debug", "Executing query", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'execution',
                    'stats': stats.__dict__,
                    'node_type': target_node.type if hasattr(target_node, 'type') else None,
                    'node_start_point': target_node.start_point if hasattr(target_node, 'start_point') else None,
                    'node_end_point': target_node.end_point if hasattr(target_node, 'end_point') else None,
                    'has_error': has_errors
                }
            })
            
            # Execute query and get captures
            captures = []
            for pattern_index, capture_dict in enumerate(query.captures(target_node)):
                for name, capture_node in capture_dict.items():
                    if self._is_node_valid(capture_node):
                        capture = QueryCapture(
                            name=name,
                            node=capture_node,
                            pattern_index=pattern_index
                        )
                        captures.append(capture)
            
            # Create result with error status
            result = QueryResult(
                captures=captures,
                stats=stats,
                is_valid=True,
                errors=["Node contains syntax errors"] if has_errors else []
            )
            
            return result
            
        except Exception as e:
            self._log("error", f"Query execution failed: {str(e)}")
            return QueryResult(
                is_valid=False,
                errors=[str(e)]
            )
            
        finally:
            # Update execution time
            duration = (time.time() - start_time) * 1000
            stats.execution_time_ms = duration
            
            self._log("debug", "Query execution completed", extra={
                'context': {
                    'source': 'tree-sitter',
                    'type': 'query',
                    'log_type': 'timing',
                    'operation': 'execute_query',
                    'duration_ms': duration
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
        """Disable a capture in future queries."""
        self._disabled_captures.add(capture)

    def disable_pattern(self, pattern_index: int) -> None:
        """Disable a pattern in future queries."""
        self._disabled_patterns.add(pattern_index)

    def find_nodes(self, tree_or_node: Union[Tree, Node], pattern_type: str, language: Optional[str] = None) -> List[Dict[str, Node]]:
        """Find nodes using native tree-sitter query methods."""
        try:
            # Lazy import PATTERN_REGISTRY to avoid circular dependency
            from GithubAnalyzer.models.analysis.pattern_registry import \
                PATTERN_REGISTRY
            lang = language or self._language_name
            pattern = PATTERN_REGISTRY.get(lang, {}).get(pattern_type)
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
        """Validate node using native tree-sitter methods."""
        errors = []
        
        # Check node state
        if not self._is_node_valid(node):
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
        """Get valid symbols that could appear at an error node."""
        if not node or not node.has_error:
            return []
            
        lang = language or self.language.name
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
        """Get matches from a query execution using native tree-sitter matches."""
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
        """Get cached query for pattern type."""
        lang = language or self.language.name
        from GithubAnalyzer.models.analysis.pattern_registry import \
            PATTERN_REGISTRY
        return self._pattern_queries.get(lang, {}).get(pattern_type)

    def _process_captures(self, captures: Dict[str, List[Node]]) -> Dict[str, List[Node]]:
        """Process captures into a dictionary mapping capture names to node lists."""
        return captures  # Tree-sitter already returns the format we want

    def find_error_nodes(self, node: Node) -> List[Node]:
        """Find error nodes in tree."""
        if not node:
            return []
        return self._traversal.find_nodes(
            node,
            lambda n: hasattr(n, 'has_error') and n.has_error
        )
        
    def find_missing_nodes(self, node: Node) -> List[Node]:
        """Find missing nodes in tree."""
        if not node:
            return []
        return self._traversal.find_nodes(
            node,
            lambda n: hasattr(n, 'is_missing') and n.is_missing
        )

    def validate_syntax(self, node: Node, language: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Validate syntax using error patterns."""
        errors = []
        
        # Find error nodes
        error_matches = self.find_nodes(node, "error", language)
        for match in error_matches:
            if 'error.syntax' in match:
                errors.append(f"Syntax error at {match['error.syntax'].start_point}")
            if 'error.missing' in match:
                errors.append(f"Missing node at {match['error.missing'].start_point}")
                
        return len(errors) == 0, errors

    def find_functions(self, target_node: Union[Node, Tree], pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find all function definitions in the given node."""
        # Use provided pattern if given, otherwise fallback to the default
        pattern = pattern if pattern is not None else self._function_pattern
        
        try:
            # Create and execute query
            query = self.language.query(pattern)
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
                self._log("debug", "Found function definition", extra={
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
                                self._log("debug", "Associated function name", extra={
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
        """Find class definitions with their components."""
        return self.find_nodes(node, "class", language)

    def find_nodes_by_type(self, node: Node, node_type: str, language: Optional[str] = None) -> List[Node]:
        """Find nodes of a specific type using native tree-sitter query."""
        lang = language or self.language.name
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

    def _is_node_valid(self, node: Optional[Node]) -> bool:
        """Check if a node is valid for capturing."""
        return (
            node is not None and
            hasattr(node, 'type') and
            hasattr(node, 'has_error') and
            not node.has_error
        ) 