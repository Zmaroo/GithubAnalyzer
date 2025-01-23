"""Tree-sitter query handling."""
from typing import List, Tuple, Dict, Any, Optional
import logging
from dataclasses import dataclass

from tree_sitter import Query, Node, Tree
from tree_sitter_language_pack import get_language

from src.GithubAnalyzer.analysis.models.tree_sitter import TreeSitterNode
from src.GithubAnalyzer.core.models.errors import LanguageError
from src.GithubAnalyzer.core.config.settings import PARSER_TIMEOUT

from .query_patterns import get_query_pattern

logger = logging.getLogger(__name__)

@dataclass
class QueryMatch:
    """Represents a query match result."""
    pattern_index: int
    captures: List[Tuple[str, Node]]
    node: Node

class TreeSitterQueryHandler:
    """Handler for tree-sitter queries with caching."""
    
    def __init__(self):
        """Initialize query handler."""
        self._queries: Dict[str, Dict[str, Query]] = {}

    def execute_query(self, query: Query, node: Node) -> List[QueryMatch]:
        """Execute query with error handling."""
        matches = []
        try:
            # Configure query limits
            query.set_timeout_micros(PARSER_TIMEOUT * 1000)
            query.set_match_limit(1000)
            
            # Get captures
            captures = query.captures(node)
            
            # Convert captures to QueryMatch format
            for name, captured_node in captures:
                if captured_node is not None:
                    matches.append(QueryMatch(
                        pattern_index=0,
                        captures=[(name, captured_node)],
                        node=captured_node
                    ))
            
            logger.debug(f"Found {len(matches)} matches")
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            
        return matches

    def create_query(self, language: str, query_string: str) -> Query:
        """Create a query with proper configuration and caching."""
        cache_key = f"{language}:{query_string}"
        if cache_key not in self._queries:
            lang = get_language(language)
            if not lang:
                raise LanguageError(f"Language {language} not found")
            
            query = Query(lang, query_string)
            query.set_match_limit(1000)
            query.set_timeout_micros(PARSER_TIMEOUT * 1000)
            
            self._queries[cache_key] = {
                'query': query,
                'pattern_count': query.pattern_count
            }
        return self._queries[cache_key]['query']
        
    def find_nodes(self, tree: Tree, language: str, query_type: str) -> List[TreeSitterNode]:
        """Find nodes matching a query pattern."""
        try:
            query_string = get_query_pattern(language, query_type)
            if not query_string:
                logger.error(f"No query pattern found for {language}/{query_type}")
                return []
                
            query = self.create_query(language, query_string)
            matches = self.execute_query(query, tree.root_node)
            
            # Extract nodes from matches
            nodes = []
            for match in matches:
                if not match.node:
                    continue
                    
                # For functions, look for the function.name capture
                if query_type == "function":
                    for capture_name, capture_node in match.captures:
                        if capture_name == "function.name":
                            nodes.append(TreeSitterNode(node=capture_node))
                            break
                else:
                    nodes.append(TreeSitterNode(node=match.node))
                    
            return nodes
            
        except Exception as e:
            logger.error(f"Find nodes failed: {e}")
            return [] 