from pathlib import Path
from typing import Dict, Any, Optional
from tree_sitter import Language, Parser, Tree, Node
from ..models.base import TreeSitterNode, ParseResult
from ..utils.logging import setup_logger
from ...config.config import LANGUAGE_MAP

logger = setup_logger(__name__)

class TreeSitterParser:
    """Tree-sitter based parser implementation"""
    
    def __init__(self):
        self.parser = Parser()
        
    def can_parse(self, file_path: str) -> bool:
        """Check if file can be parsed with tree-sitter"""
        return Path(file_path).suffix in LANGUAGE_MAP
        
    def parse(self, content: str) -> ParseResult:
        """Parse content using tree-sitter"""
        try:
            if not content.strip():
                return ParseResult(
                    ast=None,
                    semantic={},
                    errors=["Empty content"],
                    success=False
                )
                
            tree = self.parser.parse(content.encode('utf8'))
            node = self.convert_node(tree.root_node)
            
            return ParseResult(
                ast=tree,
                semantic=self.extract_semantic_info(tree),
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

    def convert_node(self, node: Node) -> TreeSitterNode:
        """Convert tree-sitter Node to our model"""
        return TreeSitterNode(
            type=node.type,
            text=node.text.decode('utf-8') if isinstance(node.text, bytes) else str(node.text),
            start_point=node.start_point,
            end_point=node.end_point,
            children=[self.convert_node(child) for child in node.children]
        )

    def extract_semantic_info(self, tree: Tree) -> Dict[str, Any]:
        """Extract semantic information from parse tree"""
        return {
            "root_type": tree.root_node.type,
            "node_count": tree.root_node.descendant_count,
            "has_error": tree.root_node.has_error,
            "range": {
                "start": tree.root_node.start_point,
                "end": tree.root_node.end_point
            }
        } 