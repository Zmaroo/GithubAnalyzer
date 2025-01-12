from typing import Dict, Any, Optional, List, Tuple
from tree_sitter import Language, Parser, Node, Tree, Query
from pathlib import Path
from .models import TreeSitterNode, ParseResult
from .utils import setup_logger, retry
from ..config.config import LANGUAGE_MAP

logger = setup_logger(__name__)

class TreeSitterService:
    """Centralized service for all tree-sitter operations"""
    
    def __init__(self, business_tools=None):
        self.tools = business_tools
        self.parser = Parser()
        self.query_cache: Dict[str, Query] = {}
    
    def parse_file(self, file_path: str, content: str) -> ParseResult:
        """Parse a file using appropriate tree-sitter parser"""
        try:
            ext = Path(file_path).suffix
            language = self._get_language(ext)
            if not language:
                return ParseResult(
                    ast=None,
                    semantic={},
                    errors=[f"No tree-sitter parser for extension: {ext}"],
                    success=False
                )
            
            return self.parse_content(content, language, file_path)
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return ParseResult(
                ast=None,
                semantic={},
                errors=[str(e)],
                success=False
            )

    @retry(max_attempts=3)
    def parse_content(self, content: str, language: Language, file_path: Optional[str] = None) -> ParseResult:
        """Parse content using tree-sitter"""
        parser = None
        try:
            if not content.strip():
                return ParseResult(
                    ast=None,
                    semantic={},
                    errors=["Empty content"],
                    success=False
                )
                
            parser = Parser()
            parser.language = language
            tree = parser.parse(content.encode('utf8'))
            node = self.convert_node(tree.root_node)
            
            return ParseResult(
                ast=tree,
                semantic=self._extract_semantic_information(tree, language, file_path) if file_path else {},
                tree_sitter_node=node,
                success=True
            )
        except Exception as e:
            logger.error(f"Error parsing content: {e}")
            return ParseResult(
                ast=None,
                semantic={},
                errors=[str(e)],
                success=False
            )
        finally:
            if parser:
                parser.reset()

    def _get_language(self, ext: str) -> Optional[Language]:
        """Get appropriate tree-sitter language for extension"""
        lang_name = LANGUAGE_MAP.get(ext.lower())
        if not lang_name:
            return None
            
        # Language loading logic moved from tree_sitter_parser.py
        # [Implementation remains the same]

    def _extract_semantic_information(self, tree: Tree, language: Language, file_path: str) -> Dict[str, Any]:
        """Extract semantic information using tree-sitter queries"""
        semantic_info = {
            "definitions": [],
            "references": [],
            "imports": [],
            "functions": [],
            "classes": [],
            "documentation": []
        }
        
        queries = self._get_language_queries(language, Path(file_path).suffix)
        
        for query_name, query in queries.items():
            captures = query.captures(tree.root_node)
            semantic_info[query_name] = self._process_captures(captures)
            
        return semantic_info

    def convert_node(self, node: Node) -> TreeSitterNode:
        """Convert tree-sitter Node to our data model"""
        return TreeSitterNode(
            type=node.type,
            text=node.text.decode('utf-8') if isinstance(node.text, bytes) else str(node.text),
            start_point=node.start_point,
            end_point=node.end_point,
            children=[self.convert_node(child) for child in node.children]
        )

    def extract_syntax_information(self, tree: Tree) -> Dict[str, Any]:
        """Extract syntax information from tree"""
        return {
            "root_type": tree.root_node.type,
            "node_count": tree.root_node.descendant_count,
            "has_error": tree.root_node.has_error,
            "range": {
                "start": tree.root_node.start_point,
                "end": tree.root_node.end_point
            }
        } 