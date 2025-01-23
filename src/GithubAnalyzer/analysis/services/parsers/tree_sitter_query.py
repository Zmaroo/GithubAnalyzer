"""TreeSitterQueryHandler for executing tree-sitter queries."""
from typing import Dict, List, Optional, Union
import logging
from tree_sitter import Query, Node, Tree, QueryError, Language
from tree_sitter_language_pack import get_language
from src.GithubAnalyzer.analysis.services.parsers.query_patterns import get_query_pattern

from src.GithubAnalyzer.core.models.errors import LanguageError
from src.GithubAnalyzer.core.utils.logging import get_logger

logger = get_logger(__name__)

class TreeSitterQueryHandler:
    """Handler for tree-sitter queries."""

    def __init__(self):
        """Initialize query handler with cache."""
        self._query_cache: Dict[str, Query] = {}
        self._language_cache: Dict[str, Language] = {}

    def create_query(self, language_name: str, query_string: str) -> Query:
        """Create a tree-sitter query.
        
        Args:
            language_name: Name of the language
            query_string: Query pattern string
            
        Returns:
            Query object
            
        Raises:
            QueryError: If query is invalid
            LanguageError: If language not found
        """
        # Check cache first
        cache_key = f"{language_name}:{query_string}"
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        try:
            # Get language
            if language_name not in self._language_cache:
                self._language_cache[language_name] = get_language(language_name)
            language = self._language_cache[language_name]

            # Create and cache query
            query = Query(language, query_string)
            self._query_cache[cache_key] = query
            return query

        except LookupError as e:
            logger.error(f"Language not found: {language_name}")
            raise LanguageError(f"Language not found: {language_name}") from e
        except QueryError as e:
            logger.error(f"Invalid query: {e}")
            raise QueryError(f"Invalid query: {e}") from e

    def execute_query(self, query: Query, node: Node) -> Dict[str, List[Node]]:
        """Execute a query on a node.

        Args:
            query: Query to execute
            node: Node to query

        Returns:
            Dict mapping capture names to lists of nodes

        Raises:
            ValueError: If node is None
        """
        if not node:
            raise ValueError("Cannot execute query on None node")

        try:
            # Execute query and get captures
            # v24 returns a dict with capture names as keys and lists of nodes as values
            return query.captures(node)
        
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {}

    def find_nodes(self, tree: Tree, language_name: str, pattern_type: str) -> List[Node]:
        """Find nodes matching a predefined pattern type.
        
        Args:
            tree: Tree to search
            language_name: Language name
            pattern_type: Type of pattern to match
            
        Returns:
            List of matching nodes
        """
        try:
            # Get pattern for type
            pattern = self._get_pattern_for_type(pattern_type)
            if not pattern:
                logger.warning(f"No pattern found for type: {pattern_type}")
                return []

            # Create and execute query
            query = self.create_query(language_name, pattern)
            captures = self.execute_query(query, tree.root_node)

            # Return all captured nodes
            return [node for capture_list in captures.values() for node in capture_list]

        except (QueryError, LanguageError) as e:
            logger.error(f"Error finding nodes: {e}")
            return []

    def _get_pattern_for_type(self, pattern_type: str) -> Optional[str]:
        """Get query pattern for a type.
        
        Args:
            pattern_type: Type of pattern
            
        Returns:
            Query pattern string or None if not found
        """
        patterns = {
            'function': """
                (function_definition) @function
            """,
            'class': """
                (class_definition) @class
            """,
            'method': """
                (function_definition
                  parent: (class_definition)) @method
            """,
            'import': """
                (import_statement) @import
                (import_from_statement) @import
            """,
            'call': """
                (call) @call
            """
        }
        return patterns.get(pattern_type) 