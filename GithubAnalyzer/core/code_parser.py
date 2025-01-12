from typing import Dict, Any, Optional, List, Generator, Tuple
from pathlib import Path
from tree_sitter import Language, Parser, Tree, Node, Query
import os
from ..config.config import LANGUAGE_MAP
from .models import TreeSitterNode
import traceback
from .utils import setup_logger
from .utils import TreeSitterUtils

logger = setup_logger(__name__)

class CodeParser:
    """Unified code parser with semantic understanding capabilities"""
    
    def __init__(self):
        self.tree_sitter = None  # Will be injected by BusinessTools
        
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a file using appropriate parser"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            parse_result = self.tree_sitter.parse_file(file_path, content)
            
            if not parse_result.success:
                return {"error": parse_result.errors[0]}
            
            return {
                "tree": parse_result.ast,
                "root_node": parse_result.tree_sitter_node,
                "syntax": parse_result.semantic,
                "semantic": self._extract_semantic_information(parse_result)
            }
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}

    def _get_language(self, ext: str) -> Optional[Language]:
        """Get appropriate tree-sitter language for extension"""
        try:
            # Check exact extension match
            lang_name = LANGUAGE_MAP.get(ext.lower())
            if not lang_name:
                return None

            # Import and return appropriate language
            if lang_name == 'python':
                import tree_sitter_python
                return Language(tree_sitter_python.language())
            elif lang_name == 'javascript':
                import tree_sitter_javascript
                return Language(tree_sitter_javascript.language())
            elif lang_name == 'typescript':
                try:
                    import tree_sitter_typescript
                    return Language(tree_sitter_typescript.language_typescript())
                except:
                    # Fallback to JavaScript
                    import tree_sitter_javascript
                    return Language(tree_sitter_javascript.language())
            elif lang_name == 'java':
                import tree_sitter_java
                return Language(tree_sitter_java.language())
            elif lang_name == 'go':
                import tree_sitter_go
                return Language(tree_sitter_go.language())
            elif lang_name == 'rust':
                import tree_sitter_rust
                return Language(tree_sitter_rust.language())
            elif lang_name == 'cpp':
                import tree_sitter_cpp
                return Language(tree_sitter_cpp.language())
            elif lang_name == 'c':
                import tree_sitter_c
                return Language(tree_sitter_c.language())
            elif lang_name == 'ruby':
                import tree_sitter_ruby
                return Language(tree_sitter_ruby.language())
            elif lang_name == 'php':
                import tree_sitter_php
                return Language(tree_sitter_php.language())
            elif lang_name == 'json':
                import tree_sitter_json
                return Language(tree_sitter_json.language())
            elif lang_name == 'yaml':
                import tree_sitter_yaml
                return Language(tree_sitter_yaml.language())
            elif lang_name == 'bash':
                import tree_sitter_bash
                return Language(tree_sitter_bash.language())
            elif lang_name == 'html':
                import tree_sitter_html
                return Language(tree_sitter_html.language())
            elif lang_name == 'css':
                import tree_sitter_css
                return Language(tree_sitter_css.language())
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting language for {ext}: {e}")
            return None

    def _convert_node(self, node: Node) -> TreeSitterNode:
        """Convert tree-sitter Node to our TreeSitterNode model"""
        return TreeSitterNode(
            type=node.type,
            text=node.text.decode('utf-8') if isinstance(node.text, bytes) else str(node.text),
            start_point=node.start_point,
            end_point=node.end_point,
            children=[self._convert_node(child) for child in node.children]
        )

    def _extract_syntax_information(self, tree: Tree) -> Dict[str, Any]:
        """Extract basic syntax information from parse tree"""
        return {
            "root_type": tree.root_node.type,
            "node_count": tree.root_node.descendant_count,
            "has_error": tree.root_node.has_error,
            "range": {
                "start": tree.root_node.start_point,
                "end": tree.root_node.end_point
            }
        }

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

    def _get_language_queries(self, language: Language, ext: str) -> Dict[str, Query]:
        """Get or create language-specific queries"""
        if ext in self.query_cache:
            return self.query_cache[ext]
            
        queries = {}
        
        # Common patterns for different languages
        query_patterns = {
            "definitions": """
                (function_definition) @function.definition
                (class_definition) @class.definition
                (variable_declaration) @variable.definition
            """,
            "references": """
                (identifier) @reference
                (variable_reference) @variable.reference
            """,
            "imports": """
                (import_statement) @import
                (include_statement) @include
            """,
            "documentation": """
                (comment) @comment
                (documentation_comment) @documentation
            """
        }
        
        # Add language-specific patterns
        if ext == '.py':
            query_patterns.update({
                "functions": "(function_definition name: (identifier) @function.name)",
                "classes": "(class_definition name: (identifier) @class.name)"
            })
        elif ext in ['.js', '.ts']:
            query_patterns.update({
                "functions": "(function_declaration name: (identifier) @function.name)",
                "classes": "(class_declaration name: (identifier) @class.name)"
            })
        
        # Create and cache queries
        for name, pattern in query_patterns.items():
            try:
                queries[name] = language.query(pattern)
            except Exception as e:
                logger.warning(f"Failed to create {name} query for {ext}: {e}")
                
        self.query_cache[ext] = queries
        return queries

    def _process_captures(self, captures: List[Tuple[Node, str]]) -> List[Dict[str, Any]]:
        """Process and structure query captures"""
        processed = []
        for node, capture_name in captures:
            processed.append({
                "type": capture_name,
                "text": node.text.decode('utf8'),
                "range": {
                    "start": node.start_point,
                    "end": node.end_point
                }
            })
        return processed

    def _extract_syntax_errors(self, tree: Tree) -> List[Dict[str, Any]]:
        """Extract syntax errors from parse tree"""
        errors = []
        cursor = tree.walk()
        
        def visit_error_nodes(cursor: Any) -> None:
            node = cursor.node
            if node.has_error:
                if node.type == 'ERROR':
                    errors.append({
                        "type": "syntax_error",
                        "range": {
                            "start": node.start_point,
                            "end": node.end_point
                        },
                        "context": self._get_error_context(node)
                    })
                    
            if cursor.goto_first_child():
                visit_error_nodes(cursor)
                while cursor.goto_next_sibling():
                    visit_error_nodes(cursor)
                cursor.goto_parent()
                
        visit_error_nodes(cursor)
        return errors

    def _get_error_context(self, error_node: Node) -> Dict[str, Any]:
        """Get context information for syntax errors"""
        return {
            "previous_valid": self._get_previous_valid_node(error_node),
            "expected_symbols": self._get_expected_symbols(error_node),
            "error_line": error_node.text.decode('utf8').split('\n')[0]
        }

    def _get_previous_valid_node(self, node: Node) -> Optional[Dict[str, Any]]:
        """Get the previous valid node before an error"""
        prev = node.prev_sibling
        while prev and (prev.type == 'ERROR' or prev.is_missing):
            prev = prev.prev_sibling
            
        if prev:
            return {
                "type": prev.type,
                "text": prev.text.decode('utf8')
            }
        return None

    def _get_expected_symbols(self, error_node: Node) -> List[str]:
        """Get list of expected symbols at error location"""
        if not hasattr(error_node, 'parse_state'):
            return []
            
        try:
            language = self.parser.language
            iterator = language.lookahead_iterator(error_node.parse_state)
            return [symbol for symbol in iterator.iter_names()]
        except Exception:
            return [] 