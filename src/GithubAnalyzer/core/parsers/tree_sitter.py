"""Tree-sitter based parser"""
from pathlib import Path
from typing import Dict, Any, Optional
from tree_sitter import Parser, Language, Tree, Node
import tree_sitter_python

from .base import BaseParser
from ..models.base import TreeSitterNode, ParseResult
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class TreeSitterParser(BaseParser):
    """Tree-sitter based parser implementation"""
    
    def __init__(self):
        """Initialize tree-sitter parser"""
        super().__init__()
        self.parser = Parser()
        self._load_languages()
        
    def _load_languages(self):
        """Load language support"""
        try:
            # Load Python language using the installed package
            PY_LANGUAGE = Language(tree_sitter_python.language(), 'python')
            self.parser.set_language(PY_LANGUAGE)
        except Exception as e:
            logger.error(f"Failed to load language support: {str(e)}")
            raise RuntimeError(f"Failed to load language support: {str(e)}")

    def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the given file"""
        return Path(file_path).suffix in ['.py', '.js', '.java']
        
    def parse(self, content: str) -> ParseResult:
        """Parse content string directly"""
        try:
            tree = self.parser.parse(bytes(content, 'utf-8'))
            converted_ast = self._convert_node(tree.root_node)
            semantic_info = self._extract_semantic_info(tree)
            
            return ParseResult(
                ast=converted_ast,
                semantic=semantic_info,
                success=True,
                raw_ast=tree
            )
        except Exception as e:
            logger.error(f"Failed to parse content: {e}")
            return ParseResult(
                ast=None,
                semantic={},
                success=False,
                errors=[f"Failed to parse content: {str(e)}"]
            )
        
    def parse_file(self, file_path: str, content: Optional[str] = None) -> ParseResult:
        """Parse file content"""
        try:
            if content is None:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
            return self.parse(content)
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return ParseResult(
                ast=None,
                semantic={},
                success=False,
                errors=[f"Failed to parse {file_path}: {str(e)}"]
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