"""Tree-sitter based parser"""
from pathlib import Path
from typing import Dict, Any, Optional
from tree_sitter import Parser, Tree, Node

# Import tree-sitter languages - handle different import patterns
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

from ..models.base import TreeSitterNode, ParseResult
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class TreeSitterParser:
    """Tree-sitter based parser implementation"""
    
    LANGUAGE_MAP = {
        # Programming Languages
        '.py': tree_sitter_python.language,
        'setup.py': tree_sitter_python.language,
        '.js': tree_sitter_javascript.language,
        '.jsx': tree_sitter_javascript.language,
        '.ts': tree_sitter_typescript.language,
        '.tsx': tree_sitter_typescript.language,
        '.java': tree_sitter_java.language,
        '.c': tree_sitter_c.language,
        '.h': tree_sitter_c.language,
        '.cpp': tree_sitter_cpp.language,
        '.hpp': tree_sitter_cpp.language,
        '.cs': tree_sitter_c_sharp.language,
        '.go': tree_sitter_go.language,
        '.rs': tree_sitter_rust.language,
        '.rb': tree_sitter_ruby.language,
        '.php': tree_sitter_php.language,
        '.scala': tree_sitter_scala.language,
        '.kt': tree_sitter_kotlin.language,
        '.lua': tree_sitter_lua.language,
        '.cu': tree_sitter_cuda.language,
        '.ino': tree_sitter_arduino.language,
        '.pde': tree_sitter_arduino.language,
        '.m': tree_sitter_matlab.language,
        '.groovy': tree_sitter_groovy.language,
        'build.gradle': tree_sitter_groovy.language,
        
        # Build Systems
        'CMakeLists.txt': tree_sitter_cmake.language,
        '.cmake': tree_sitter_cmake.language,
        
        # Web Technologies
        '.html': tree_sitter_html.language,
        '.css': tree_sitter_css.language,
        
        # Data & Config
        '.json': tree_sitter_json.language,
        '.yaml': tree_sitter_yaml.language,
        '.yml': tree_sitter_yaml.language,
        '.toml': tree_sitter_toml.language,
        '.xml': tree_sitter_xml.language,
        
        # Query Languages
        '.sql': tree_sitter_sql.language,
        
        # Documentation
        '.md': tree_sitter_markdown.language,
        '.markdown': tree_sitter_markdown.language,
        'README': tree_sitter_markdown.language,
        'README.md': tree_sitter_markdown.language,
        'CHANGELOG': tree_sitter_markdown.language,
        'CHANGELOG.md': tree_sitter_markdown.language,
        'CONTRIBUTING': tree_sitter_markdown.language,
        'CONTRIBUTING.md': tree_sitter_markdown.language,
        'LICENSE.md': tree_sitter_markdown.language,
        
        # Shell Scripts
        '.sh': tree_sitter_bash.language,
        '.bash': tree_sitter_bash.language,
        '.env': tree_sitter_bash.language
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
                name = path.name.upper()
                
                # Special handling for markdown files
                if name.startswith(('README', 'CHANGELOG', 'CONTRIBUTING', 'LICENSE')):
                    self.parser.set_language(markdown_language)
                elif not key in self.LANGUAGE_MAP:
                    key = path.name.lower()
                    if key in self.LANGUAGE_MAP:
                        self.parser.set_language(self.LANGUAGE_MAP[key])
                else:
                    self.parser.set_language(self.LANGUAGE_MAP[key])
            
            # Parse content - tree-sitter expects bytes
            tree = self.parser.parse(bytes(content, 'utf8'))
            
            # Special validation for markdown files
            if file_path and (Path(file_path).suffix.lower() == '.md' or 
                            Path(file_path).name.upper().startswith(('README', 'CHANGELOG', 'CONTRIBUTING', 'LICENSE'))):
                if not self._validate_markdown(tree):
                    return ParseResult(
                        ast=None,
                        semantic={},
                        errors=["Invalid markdown structure"],
                        success=False
                    )
            
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
    
    def _validate_markdown(self, tree: Tree) -> bool:
        """Validate markdown structure"""
        try:
            root = tree.root_node
            
            # Check for basic markdown structure
            if not root or root.has_error:
                return False
                
            # Validate first line is a heading
            first_heading = None
            for child in root.children:
                if child.type == 'atx_heading' or child.type == 'setext_heading':
                    first_heading = child
                    break
                    
            if not first_heading:
                return False
                
            # Validate code blocks
            for node in root.children:
                if node.type == 'fenced_code_block':
                    if not self._validate_code_block(node):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating markdown: {e}")
            return False
    
    def _validate_code_block(self, node: Node) -> bool:
        """Validate markdown code block"""
        try:
            # Check for language info
            info_string = None
            for child in node.children:
                if child.type == 'info_string':
                    info_string = child
                    break
            
            # Code blocks should have language specified
            if not info_string:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating code block: {e}")
            return False 