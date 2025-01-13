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
            # Load Python language
            PY_LANGUAGE = Language('build/languages.so', 'python')
            self.parser.set_language(PY_LANGUAGE)
        except Exception as e:
            raise RuntimeError(f"Failed to load language support: {str(e)}")
        
    def parse_file(self, file_path):
        """Parse file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = self.parser.parse(bytes(content, 'utf-8'))
            return ParseResult(
                ast=tree,
                success=True
            )
        except Exception as e:
            return ParseResult(
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