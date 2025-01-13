"""Tree-sitter based parser"""
from pathlib import Path
from typing import Dict, Any, Optional
from tree_sitter import Language, Parser, Tree, Node
from tree_sitter_python import language as py_language
from ..models.base import TreeSitterNode, ParseResult
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class TreeSitterParser:
    """Tree-sitter based parser implementation"""
    
    def __init__(self):
        """Initialize tree-sitter parser"""
        try:
            self.parser = Parser()
            # Use pre-installed Python language
            self.parser.set_language(py_language)
            logger.info("Tree-sitter parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tree-sitter: {e}")
            self.parser = None
        
    def can_parse(self, file_path: str) -> bool:
        """Check if file can be parsed with tree-sitter"""
        return Path(file_path).suffix == '.py' and self.parser is not None
        
    def parse(self, content: str) -> ParseResult:
        """Parse content using tree-sitter"""
        try:
            if not self.parser:
                return ParseResult(
                    ast=None,
                    semantic={},
                    errors=["Tree-sitter not initialized"],
                    success=False
                )
                
            if not content or not content.strip():
                return ParseResult(
                    ast=None,
                    semantic={},
                    errors=["Empty content"],
                    success=False
                )
                
            # Parse content - tree-sitter expects bytes
            tree = self.parser.parse(bytes(content, 'utf8'))
            if not tree or tree.root_node.has_error:
                return ParseResult(
                    ast=None,
                    semantic={},
                    errors=["Parsing failed"],
                    success=False
                )
                
            # Convert tree-sitter node to our model
            node = self._convert_node(tree.root_node)
            semantic_info = self._extract_semantic_info(tree)
            
            return ParseResult(
                ast=tree,
                semantic=semantic_info,
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
    
    def _convert_node(self, node: Node) -> TreeSitterNode:
        """Convert tree-sitter Node to our model"""
        try:
            return TreeSitterNode(
                type=node.type,
                text=node.text.decode('utf-8') if isinstance(node.text, bytes) else str(node.text),
                start_point=node.start_point,
                end_point=node.end_point,
                children=[self._convert_node(child) for child in node.children]
            )
        except Exception as e:
            logger.error(f"Error converting node: {e}")
            return TreeSitterNode(
                type="ERROR",
                text=str(e),
                start_point=(0,0),
                end_point=(0,0),
                children=[]
            )
    
    def _extract_semantic_info(self, tree: Tree) -> Dict[str, Any]:
        """Extract semantic information from parse tree"""
        try:
            return {
                "root_type": tree.root_node.type,
                "node_count": tree.root_node.descendant_count,
                "has_error": tree.root_node.has_error,
                "range": {
                    "start": tree.root_node.start_point,
                    "end": tree.root_node.end_point
                },
                "syntax_errors": [
                    {
                        "node": child.type,
                        "position": child.start_point
                    }
                    for child in tree.root_node.children 
                    if child.has_error
                ]
            }
        except Exception as e:
            logger.error(f"Error extracting semantic info: {e}")
            return {} 