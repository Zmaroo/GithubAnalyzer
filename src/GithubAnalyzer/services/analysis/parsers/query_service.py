"""Tree-sitter query service for pattern matching."""
import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, TypeVar, Union

from tree_sitter import Language, Node, Parser, Point, Query, QueryError, Tree
from tree_sitter_language_pack import get_binding, get_language, get_parser

# Analysis models
from GithubAnalyzer.models.analysis.query import (QueryCapture, QueryExecutor,
                                                  QueryOptimizationSettings,
                                                  QueryPattern, QueryResult,
                                                  QueryStats)
from GithubAnalyzer.models.analysis.types import LanguageId
# Core models
from GithubAnalyzer.models.core.ast import NodeDict, NodeList
from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.models.core.traversal import TreeSitterTraversal
from GithubAnalyzer.models.core.tree_sitter_core import (
    get_node_text, get_node_type, get_node_range, is_valid_node,
    node_to_dict, iter_children
)
# Services
from GithubAnalyzer.services.parsers.core.base_parser_service import \
    BaseParserService
from GithubAnalyzer.services.parsers.core.language_service import \
    LanguageService
from GithubAnalyzer.services.parsers.core.query_handler import \
    TreeSitterQueryHandler
# Utils
from GithubAnalyzer.utils.logging import get_logger
from GithubAnalyzer.utils.timing import timer

# Initialize logger with proper configuration
logger = get_logger(__name__)

# Type variable for better type hints
T = TypeVar('T', bound=Node)

@dataclass
class QueryService(BaseParserService):
    """Service for executing tree-sitter queries."""
    
    _query_handler: TreeSitterQueryHandler = field(default_factory=TreeSitterQueryHandler)
    
    def __post_init__(self):
        """Initialize query service."""
        super().__post_init__()
        self._log("debug", "Query service initialized")
        
    @timer
    def execute_query(self, language: str, pattern_name: str, content: str) -> QueryResult:
        """Execute a query on content."""
        return self._query_handler.execute_query(language, pattern_name, content)
        
    def get_pattern(self, language: str, pattern_name: str) -> Optional[str]:
        """Get a query pattern."""
        return self._query_handler.get_pattern(language, pattern_name)
        
    def get_language_patterns(self, language: str) -> Optional[Dict[str, QueryPattern]]:
        """Get all patterns for a language."""
        return self._query_handler.get_language_patterns(language)
        
    def get_optimization_settings(self, language: str) -> QueryOptimizationSettings:
        """Get optimization settings for a language."""
        return self._query_handler.get_optimization_settings(language)