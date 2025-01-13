"""Tree-sitter based parser"""
from pathlib import Path
from typing import Dict, Any, Optional
from tree_sitter import Parser, Language, Tree, Node

# Import tree-sitter languages
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_java
import tree_sitter_go
import tree_sitter_rust
import tree_sitter_cpp
import tree_sitter_c
import tree_sitter_c_sharp
import tree_sitter_ruby
import tree_sitter_php
import tree_sitter_scala
import tree_sitter_kotlin
import tree_sitter_html
import tree_sitter_css
import tree_sitter_json
import tree_sitter_yaml
import tree_sitter_toml
import tree_sitter_xml
import tree_sitter_bash
import tree_sitter_lua
import tree_sitter_markdown
import tree_sitter_cmake
import tree_sitter_arduino
import tree_sitter_cuda
import tree_sitter_groovy
import tree_sitter_matlab
import tree_sitter_typescript
import tree_sitter_sql

from ..models.base import TreeSitterNode, ParseResult
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class TreeSitterParser:
    """Tree-sitter based parser implementation"""
    
    def __init__(self):
        """Initialize tree-sitter parser"""
        try:
            self.parser = Parser()
            self._init_languages()
            # Default to Python language
            self.parser.language = self.LANGUAGE_MAP['.py']
            logger.info("Tree-sitter parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize tree-sitter: {e}")
            self.parser = None
            
    def _init_languages(self):
        """Initialize language objects"""
        self.LANGUAGE_MAP = {
            # Programming Languages
            '.py': Language(tree_sitter_python.language()),
            'setup.py': Language(tree_sitter_python.language()),
            '.js': Language(tree_sitter_javascript.language()),
            '.jsx': Language(tree_sitter_javascript.language()),
            '.ts': Language(tree_sitter_typescript.language()),
            '.tsx': Language(tree_sitter_typescript.language()),
            '.java': Language(tree_sitter_java.language()),
            '.c': Language(tree_sitter_c.language()),
            '.h': Language(tree_sitter_c.language()),
            '.cpp': Language(tree_sitter_cpp.language()),
            '.hpp': Language(tree_sitter_cpp.language()),
            '.cs': Language(tree_sitter_c_sharp.language()),
            '.go': Language(tree_sitter_go.language()),
            '.rs': Language(tree_sitter_rust.language()),
            '.rb': Language(tree_sitter_ruby.language()),
            '.php': Language(tree_sitter_php.language()),
            '.scala': Language(tree_sitter_scala.language()),
            '.kt': Language(tree_sitter_kotlin.language()),
            '.lua': Language(tree_sitter_lua.language()),
            '.cu': Language(tree_sitter_cuda.language()),
            '.ino': Language(tree_sitter_arduino.language()),
            '.pde': Language(tree_sitter_arduino.language()),
            '.m': Language(tree_sitter_matlab.language()),
            '.groovy': Language(tree_sitter_groovy.language()),
            'build.gradle': Language(tree_sitter_groovy.language()),
            
            # Build Systems
            'CMakeLists.txt': Language(tree_sitter_cmake.language()),
            '.cmake': Language(tree_sitter_cmake.language()),
            
            # Web Technologies
            '.html': Language(tree_sitter_html.language()),
            '.css': Language(tree_sitter_css.language()),
            
            # Data & Config
            '.json': Language(tree_sitter_json.language()),
            '.yaml': Language(tree_sitter_yaml.language()),
            '.yml': Language(tree_sitter_yaml.language()),
            '.toml': Language(tree_sitter_toml.language()),
            '.xml': Language(tree_sitter_xml.language()),
            
            # Documentation
            '.md': Language(tree_sitter_markdown.language()),
            '.markdown': Language(tree_sitter_markdown.language()),
            'README': Language(tree_sitter_markdown.language()),
            'README.md': Language(tree_sitter_markdown.language()),
            'CHANGELOG': Language(tree_sitter_markdown.language()),
            'CHANGELOG.md': Language(tree_sitter_markdown.language()),
            'CONTRIBUTING': Language(tree_sitter_markdown.language()),
            'CONTRIBUTING.md': Language(tree_sitter_markdown.language()),
            'LICENSE.md': Language(tree_sitter_markdown.language()),
            
            # Query Languages
            '.sql': Language(tree_sitter_sql.language()),
            
            # Shell Scripts
            '.sh': Language(tree_sitter_bash.language()),
            '.bash': Language(tree_sitter_bash.language()),
            '.env': Language(tree_sitter_bash.language())
        }
        
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
                    self.parser.language = self.LANGUAGE_MAP[key]
                
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