"""Tree-sitter based parser"""
from pathlib import Path
from typing import Dict, Any, Optional, List
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
            # Load Python language using the language() function directly
            # The Language constructor only takes one argument - the language object
            PY_LANGUAGE = Language(tree_sitter_python.language())
            self.parser.language = PY_LANGUAGE
        except Exception as e:
            logger.error(f"Failed to load language support: {str(e)}")
            raise RuntimeError(f"Failed to load language support: {str(e)}")

    def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the given file"""
        return Path(file_path).suffix in ['.py']
        
    def parse(self, content: str) -> ParseResult:
        """Parse content string directly"""
        try:
            if not self.parser.language:
                return ParseResult(
                    ast=None,
                    semantic={},
                    success=False,
                    errors=["Parser language not initialized"]
                )

            # Convert string to bytes for tree-sitter
            encoded_content = bytes(content, 'utf-8')
            tree = self.parser.parse(encoded_content)
            
            if tree is None:
                return ParseResult(
                    ast=None,
                    semantic={},
                    success=False,
                    errors=["Failed to generate parse tree"]
                )
                
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
            if not self.can_parse(file_path):
                return ParseResult(
                    ast=None,
                    semantic={},
                    success=False,
                    errors=[f"Unsupported file type: {file_path}"]
                )
                
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
            # Initialize semantic info
            semantic_info = {
                "root_type": tree.root_node.type,
                "node_count": tree.root_node.descendant_count,
                "has_error": tree.root_node.has_error,
                "range": {
                    "start": tree.root_node.start_point,
                    "end": tree.root_node.end_point
                },
                "functions": [],
                "classes": [],
                "syntax_errors": []
            }

            # Create cursor for efficient tree traversal
            cursor = tree.walk()
            visited_children = False

            # Walk the tree to find functions and classes
            while True:
                if not visited_children:
                    node = cursor.node
                    
                    # Handle function definitions
                    if node.type == 'function_definition':
                        name_node = node.child_by_field_name('name')
                        if name_node:
                            semantic_info["functions"].append({
                                "name": name_node.text.decode('utf-8') if isinstance(name_node.text, bytes) else str(name_node.text),
                                "start": node.start_point,
                                "end": node.end_point,
                                "parameters": self._extract_parameters(node)
                            })
                    
                    # Handle class definitions
                    elif node.type == 'class_definition':
                        name_node = node.child_by_field_name('name')
                        if name_node:
                            semantic_info["classes"].append({
                                "name": name_node.text.decode('utf-8') if isinstance(name_node.text, bytes) else str(name_node.text),
                                "start": node.start_point,
                                "end": node.end_point
                            })
                    
                    # Handle syntax errors
                    if node.has_error:
                        semantic_info["syntax_errors"].append({
                            "node": node.type,
                            "position": node.start_point,
                            "text": node.text.decode('utf-8') if isinstance(node.text, bytes) else str(node.text)
                        })

                    if not cursor.goto_first_child():
                        visited_children = True
                elif cursor.goto_next_sibling():
                    visited_children = False
                elif not cursor.goto_parent():
                    break

            return semantic_info

        except Exception as e:
            logger.error(f"Error extracting semantic info: {e}")
            return {
                "root_type": tree.root_node.type,
                "node_count": 0,
                "has_error": True,
                "functions": [],
                "classes": [],
                "syntax_errors": [{"error": str(e)}]
            }

    def _extract_parameters(self, function_node: Node) -> List[Dict[str, Any]]:
        """Extract function parameters information"""
        parameters = []
        params_node = function_node.child_by_field_name('parameters')
        
        if params_node:
            for param in params_node.children:
                if param.type != ',' and param.type != '(' and param.type != ')':
                    param_info = {
                        "name": param.text.decode('utf-8') if isinstance(param.text, bytes) else str(param.text),
                        "type": param.type
                    }
                    
                    # Try to get type annotation if it exists
                    type_node = param.child_by_field_name('type')
                    if type_node:
                        param_info["annotation"] = type_node.text.decode('utf-8') if isinstance(type_node.text, bytes) else str(type_node.text)
                        
                    parameters.append(param_info)
                    
        return parameters 