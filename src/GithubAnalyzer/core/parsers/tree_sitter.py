"""Tree-sitter based parser"""
from pathlib import Path
from typing import Dict, Any, Optional
from tree_sitter import Parser, Tree, Node

# Import all available tree-sitter languages
from tree_sitter_arduino import language as arduino_language
from tree_sitter_bash import language as bash_language
from tree_sitter_c import language as c_language
from tree_sitter_c_sharp import language as csharp_language
from tree_sitter_cmake import language as cmake_language
from tree_sitter_cpp import language as cpp_language
from tree_sitter_css import language as css_language
from tree_sitter_cuda import language as cuda_language
from tree_sitter_go import language as go_language
from tree_sitter_groovy import language as groovy_language
from tree_sitter_html import language as html_language
from tree_sitter_java import language as java_language
from tree_sitter_javascript import language as javascript_language
from tree_sitter_json import language as json_language
from tree_sitter_kotlin import language as kotlin_language
from tree_sitter_lua import language as lua_language
from tree_sitter_markdown import language as markdown_language
from tree_sitter_matlab import language as matlab_language
from tree_sitter_php import language as php_language
from tree_sitter_python import language as python_language
from tree_sitter_ruby import language as ruby_language
from tree_sitter_rust import language as rust_language
from tree_sitter_scala import language as scala_language
from tree_sitter_sql import language as sql_language
from tree_sitter_toml import language as toml_language
from tree_sitter_typescript import language as typescript_language
from tree_sitter_xml import language as xml_language
from tree_sitter_yaml import language as yaml_language

from ..models.base import TreeSitterNode, ParseResult
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class TreeSitterParser:
    """Tree-sitter based parser implementation"""
    
    LANGUAGE_MAP = {
        # Programming Languages
        '.py': python_language,
        'setup.py': python_language,
        '.js': javascript_language,
        '.jsx': javascript_language,
        '.ts': typescript_language,
        '.tsx': typescript_language,
        '.java': java_language,
        '.c': c_language,
        '.h': c_language,
        '.cpp': cpp_language,
        '.hpp': cpp_language,
        '.cs': csharp_language,
        '.go': go_language,
        '.rs': rust_language,
        '.rb': ruby_language,
        '.php': php_language,
        '.scala': scala_language,
        '.kt': kotlin_language,
        '.lua': lua_language,
        '.cu': cuda_language,
        '.ino': arduino_language,
        '.pde': arduino_language,
        '.m': matlab_language,
        '.groovy': groovy_language,
        'build.gradle': groovy_language,
        
        # Build Systems
        'CMakeLists.txt': cmake_language,
        '.cmake': cmake_language,
        
        # Web Technologies
        '.html': html_language,
        '.css': css_language,
        
        # Data & Config
        '.json': json_language,
        '.yaml': yaml_language,
        '.yml': yaml_language,
        '.toml': toml_language,
        '.xml': xml_language,
        
        # Query Languages
        '.sql': sql_language,
        
        # Documentation
        '.md': markdown_language,
        '.markdown': markdown_language,
        
        # Shell Scripts
        '.sh': bash_language,
        '.bash': bash_language,
        '.env': bash_language
    }
    
    def __init__(self):
        """Initialize tree-sitter parser"""
        try:
            self.parser = Parser()
            # Default to Python language
            self.parser.set_language(python_language)
            logger.info("Tree-sitter parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tree-sitter: {e}")
            self.parser = None
        
    def can_parse(self, file_path: str) -> bool:
        """Check if file can be parsed with tree-sitter"""
        path = Path(file_path)
        return (path.suffix.lower() in self.LANGUAGE_MAP or 
                path.name.lower() in self.LANGUAGE_MAP) and self.parser is not None
        
    def parse(self, content: str, file_path: Optional[str] = None) -> ParseResult:
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
            
            # Set language based on file extension or name
            if file_path:
                path = Path(file_path)
                key = path.suffix.lower()
                if not key in self.LANGUAGE_MAP:
                    key = path.name.lower()
                if key in self.LANGUAGE_MAP:
                    self.parser.set_language(self.LANGUAGE_MAP[key])
                
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