"""Parser service for code analysis."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Set, Union

from tree_sitter import Tree

from GithubAnalyzer.models.analysis.tree_sitter import TreeSitterResult
from GithubAnalyzer.models.core.ast import ParseResult
from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.services.analysis.parsers.query_service import \
    TreeSitterQueryHandler
from GithubAnalyzer.services.parsers.core.base_parser_service import \
    BaseParserService
from GithubAnalyzer.utils.logging import get_logger
from GithubAnalyzer.utils.timing import timer

logger = get_logger(__name__)

@dataclass
class AnalysisParserService:
    """Service for parsing files with analysis capabilities."""
    
    def __post_init__(self):
        """Initialize the parser service."""
        self._query_handler = TreeSitterQueryHandler()
        self._log("debug", "Analysis parser service initialized")
    
    @timer
    def parse_content(self, content: str, language: str) -> ParseResult:
        """Parse content with analysis capabilities."""
        try:
            # Get base parse result with tree
            result = super().parse_content(content, language)
            if not result.tree:
                return result
                
            # Create TreeSitterResult for analysis
            ts_result = TreeSitterResult(
                tree=result.tree,
                is_valid=not result.tree.root_node.has_error,
                language=language,
                node_count=result.tree.root_node.descendant_count,
                error_count=len(self._query_handler.find_error_nodes(result.tree.root_node)),
                depth=self._get_tree_depth(result.tree.root_node)
            )
            
            # Extract nodes
            ts_result.functions = self._query_handler.find_functions(result.tree.root_node, language)
            ts_result.classes = self._query_handler.find_nodes(result.tree, "class", language)
            ts_result.imports = self._query_handler.find_nodes(result.tree, "import", language)
            
            # Get any missing or error nodes
            missing_nodes = self._query_handler.find_missing_nodes(result.tree.root_node)
            error_nodes = self._query_handler.find_error_nodes(result.tree.root_node)
            
            # Update parse result with analysis data
            result.functions = ts_result.functions
            result.classes = ts_result.classes
            result.imports = ts_result.imports
            result.missing_nodes = missing_nodes
            result.error_nodes = error_nodes
            
            self._log("debug", "Content parsed with analysis",
                     language=language,
                     parse_result=ts_result.__dict__)
            
            return result
            
        except Exception as e:
            self._log("error", "Failed to parse content with analysis",
                     language=language,
                     error=str(e))
            return super().parse_content(content, language)

    def _get_tree_depth(self, node: Tree) -> int:
        """Get the maximum depth of a tree."""
        if not node.children:
            return 0
        return 1 + max(self._get_tree_depth(child) for child in node.children)
        
    def get_supported_languages(self) -> Set[str]:
        """Get set of supported languages."""
        return self._language_service.supported_languages 