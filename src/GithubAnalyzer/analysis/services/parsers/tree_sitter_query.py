"""Tree-sitter query handling."""
from typing import List, Tuple
import logging
from tree_sitter import Query, QueryError

from src.GithubAnalyzer.analysis.models.tree_sitter import TreeSitterQueryError
from src.GithubAnalyzer.core.config.settings import settings

logger = logging.getLogger(__name__)

MAX_QUERY_MATCHES = 1000
QUERY_TIMEOUT_MS = 5000

class TreeSitterQueryHandler:
    """Handles Tree-sitter queries."""
    
    def __init__(self, languages):
        self.languages = languages

    def create_query(self, language: str, query_string: str) -> Tuple[Query, List[TreeSitterQueryError]]:
        """Create a tree-sitter query with error handling."""
        try:
            logger.debug("Creating query for language %s", language)
            lang = self.languages[language]
            query = Query(lang, query_string)
            
            query.disable_pattern(0)
            query.set_match_limit(MAX_QUERY_MATCHES)
            query.set_timeout_micros(settings.parser_timeout * 1000)
            
            errors = []
            for pattern_index, pattern in enumerate(query.patterns):
                try:
                    if hasattr(pattern, 'validate_predicates'):
                        pattern.validate_predicates()
                except QueryError as e:
                    errors.append(TreeSitterQueryError(
                        message=str(e),
                        query=query_string,
                        pattern_index=pattern_index
                    ))
            
            return query, errors
            
        except Exception as e:
            logger.error("Failed to create query: %s", e)
            raise 