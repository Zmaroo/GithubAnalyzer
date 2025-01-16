"""Tree-sitter parser implementation."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Generator
from tree_sitter import Language as TSLanguage, Parser as TSParser, Node, Tree, TreeCursor, Query
import logging
import importlib

from ....config.language_config import TREE_SITTER_LANGUAGES
from ....models.analysis.ast import ParseResult
from ....models.core.errors import ParserError, FileOperationError
from ....utils.file_utils import get_file_type, is_binary_file, validate_file_path
from .base import BaseParser

logger = logging.getLogger(__name__)

def tree_sitter_logger(msg: str) -> None:
    """Logger function for Tree-sitter parsing."""
    logger.debug(f"Tree-sitter: {msg}")

class TreeSitterParser(BaseParser):
    """Parser implementation using tree-sitter."""

    # Language-specific query patterns
    _QUERY_PATTERNS = {
        "python": """
            ;; Match complete function definitions
            (function_definition
              name: (identifier) @function.name) @function.def

            ;; Match error recovery cases
            (ERROR
              [(function_definition
                name: (identifier) @function.name)
               (expression_statement
                 (call
                   function: (identifier) @function.name))] @error.function)
        """,
        "javascript": """
            ;; Match function declarations
            (function_declaration
              name: (identifier) @name) @function
            
            ;; Match method definitions
            (method_definition
              name: (property_identifier) @name) @function
            
            ;; Match error recovery cases
            (ERROR
              [(function_declaration
                name: (identifier) @name)
               (identifier) @name]) @error
        """,
        "typescript": """
            ;; Match function declarations
            (function_declaration
              name: (identifier) @name) @function
            
            ;; Match method definitions
            (method_definition
              name: (property_identifier) @name) @function
            
            ;; Match arrow functions
            (variable_declarator
              name: (identifier) @name
              value: (arrow_function)) @function
        """,
        "java": """
            ;; Match method declarations
            (method_declaration
              name: (identifier) @name) @function
            
            ;; Match class declarations
            (class_declaration
              name: (identifier) @name) @class
        """,
        "cpp": """
            ;; Match function definitions
            (function_definition
              declarator: (function_declarator
                declarator: (identifier) @name)) @function
            
            ;; Match class definitions
            (class_specifier
              name: (type_identifier) @name) @class
        """,
        "go": """
            ;; Match function declarations
            (function_declaration
              name: (identifier) @name) @function
            
            ;; Match method declarations
            (method_declaration
              name: (field_identifier) @name) @function
        """,
        "tsx": """
            ;; Match function declarations
            (function_declaration
              name: (identifier) @name) @function

            ;; Match arrow functions with variable declarations
            (variable_declarator
              name: (identifier) @name
              value: (arrow_function)) @function

            ;; Match class methods
            (method_definition
              name: (property_identifier) @name) @function

            ;; Match public class fields with arrow functions
            (public_field_definition
              name: (property_identifier) @name
              value: (arrow_function)) @function
        """,
    }

    def __init__(self, encoding: str = "utf8", debug: bool = False):
        """Initialize Tree-sitter parser."""
        self.initialized = False
        self._encoding = encoding
        self._parsers: Dict[str, TSParser] = {}
        self._languages: Dict[str, TSLanguage] = {}
        self._debug = debug
        self._queries: Dict[str, Query] = {}
        
    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize parsers for supported languages."""
        try:
            logger.info("Initializing tree-sitter parsers")
            
            # Use provided languages or all configured languages
            langs_to_init = languages or TREE_SITTER_LANGUAGES.keys()
            
            for lang in langs_to_init:
                if lang not in TREE_SITTER_LANGUAGES:
                    logger.warning(f"Language {lang} not configured, skipping")
                    continue
                    
                config = TREE_SITTER_LANGUAGES[lang]
                try:
                    # Initialize parser
                    parser = TSParser()
                    language = self._load_language(lang)
                    parser.language = language
                    
                    self._parsers[lang] = parser
                    self._languages[lang] = language
                    
                    logger.debug(f"Initialized {lang} parser")
                    
                    # Initialize queries for this language
                    self._initialize_queries(lang)
                    logger.debug(f"Initialized {lang} queries")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize {lang}: {str(e)}")
                    raise ParserError(f"Failed to initialize {lang}: {str(e)}")
            
            self.initialized = True
            logger.info("Tree-sitter parsers initialized")
            
        except Exception as e:
            logger.error(f"Parser initialization failed: {str(e)}")
            raise ParserError(f"Parser initialization failed: {str(e)}")

    def parse(self, content: Union[str, bytes], language: str) -> ParseResult:
        """Parse source code using tree-sitter."""
        try:
            # Get parser for language
            parser = self._parsers[language]
            
            # Parse content
            if isinstance(content, str):
                content = content.encode('utf8')
            
            # Debug logging - just use our logger
            if self._debug:
                logger.debug(f"Tree-sitter [{language}]: Parsing content")
            
            tree = parser.parse(content)
            if not tree:
                raise ParserError("Parser failed to produce AST")
            
            # Debug print AST structure
            if self._debug:
                self._debug_print_ast(tree.root_node)
            
            # Get analysis results
            analysis = self._analyze_tree(tree, language)
            
            # Convert content back to string for metadata
            raw_content = content.decode('utf8') if isinstance(content, bytes) else content
            
            return ParseResult(
                ast=tree,
                language=language,
                is_valid=not tree.root_node.has_error,
                line_count=len(content.splitlines()),
                node_count=tree.root_node.descendant_count,
                errors=self._get_syntax_errors(tree.root_node),
                metadata={
                    "encoding": self._encoding,
                    "raw_content": raw_content,
                    "root_type": tree.root_node.type,
                    "analysis": analysis
                }
            )
            
        except Exception as e:
            raise ParserError(f"Failed to parse {language} content: {str(e)}")

    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """Parse a source code file."""
        try:
            # Validate and normalize path
            path = validate_file_path(file_path)
            if not isinstance(path, Path):
                raise ParserError(f"Invalid file path: {file_path}")
            
            if not path.exists():
                raise ParserError(f"File not found: {path}")

            try:
                if is_binary_file(str(path)):
                    raise ParserError(f"File {path} is not a text file")
            except FileOperationError as e:
                raise ParserError(str(e))

            language = self._get_language_for_file(path)
            if not language:
                raise ParserError(f"Unsupported file extension: {path.suffix}")

            try:
                with open(path, 'r', encoding=self._encoding) as f:
                    content = f.read()
            except UnicodeDecodeError:
                raise ParserError(f"File {path} is not a valid text file")

            result = self.parse(content, language)
            result.metadata["file_path"] = str(path)
            return result
        except Exception as e:
            if isinstance(e, ParserError):
                raise e
            raise ParserError(f"Failed to parse file {file_path}: {str(e)}")

    def cleanup(self) -> None:
        """Clean up parser resources."""
        self._parsers.clear()
        self._languages.clear()
        self._queries.clear()
        self.initialized = False

    def _get_language_for_file(self, file_path: Union[str, Path]) -> Optional[str]:
        """Get language for file based on extension."""
        return get_file_type(str(file_path))

    def _count_nodes(self, node: Node) -> int:
        """Count nodes in AST recursively."""
        count = 1  # Count current node
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def _get_errors(self, node: Node) -> List[str]:
        """Extract syntax errors from AST.
        
        According to tree-sitter docs:
        - ERROR nodes represent syntax errors
        - has_error indicates a node contains errors
        - Missing nodes are inserted for error recovery
        """
        errors = []
        cursor = node.walk()
        
        def visit(cursor: TreeCursor) -> None:
            if cursor.node.type == "ERROR":
                errors.append(f"Syntax error at line {cursor.node.start_point[0] + 1}")
            elif cursor.node.is_missing:
                errors.append(f"Missing node at line {cursor.node.start_point[0] + 1}")
            
            if cursor.goto_first_child():
                visit(cursor)
                cursor.goto_parent()
            
            if cursor.goto_next_sibling():
                visit(cursor)
        
        visit(cursor)
        return errors

    def _analyze_tree(self, tree: Tree, language: str) -> Dict[str, Any]:
        """Analyze AST for additional information."""
        root_node = tree.root_node
        
        return {
            "functions": self._get_functions(root_node, language),
            "errors": self._get_syntax_errors(root_node),
            "metrics": {
                "depth": self._get_tree_depth(root_node),
                "complexity": self._estimate_complexity(root_node),
            }
        }

    def _get_functions(self, root_node: Node, language: str) -> Dict[str, Dict[str, int]]:
        """Extract function definitions from AST using tree-sitter traversal."""
        functions = {}
        cursor = root_node.walk()
        visited_children = False
        
        try:
            while True:
                if not visited_children:
                    node = cursor.node
                    
                    # Check for function declarations/definitions
                    if node.type in ["function_declaration", "function_definition", "method_definition"]:
                        name_node = node.child_by_field_name("name")
                        if name_node and name_node.type in ["identifier", "property_identifier"]:
                            name = name_node.text.decode('utf8')
                            functions[name] = {
                                'start': node.start_byte,
                                'end': node.end_byte
                            }
                            if self._debug:
                                logger.debug(f"Added function: {name}")
                    
                    # Check for arrow functions
                    elif node.type == "variable_declarator":
                        name_node = node.child_by_field_name("name")
                        value_node = node.child_by_field_name("value")
                        if (name_node and name_node.type == "identifier" and 
                            value_node and value_node.type == "arrow_function"):
                            name = name_node.text.decode('utf8')
                            functions[name] = {
                                'start': node.start_byte,
                                'end': node.end_byte
                            }
                            if self._debug:
                                logger.debug(f"Added arrow function: {name}")
                    
                    # Check for class fields with arrow functions
                    elif node.type == "public_field_definition":
                        name_node = node.child_by_field_name("name")
                        value_node = node.child_by_field_name("value")
                        if (name_node and name_node.type == "property_identifier" and 
                            value_node and value_node.type == "arrow_function"):
                            name = name_node.text.decode('utf8')
                            functions[name] = {
                                'start': node.start_byte,
                                'end': node.end_byte
                            }
                            if self._debug:
                                logger.debug(f"Added class field function: {name}")
                    
                    # Check for error nodes that might contain functions
                    elif node.type == "ERROR":
                        # Look for function-like patterns in error node
                        for child in node.children:
                            # Python-style function definition
                            if child.type == "def":
                                for sibling in child.next_sibling.children:
                                    if sibling.type == "identifier":
                                        name = sibling.text.decode('utf8')
                                        functions[name] = {
                                            'start': child.start_byte,
                                            'end': node.end_byte
                                        }
                                        if self._debug:
                                            logger.debug(f"Added error recovery function: {name}")
                                        break
                            # JavaScript/TypeScript function declaration
                            elif child.type == "function_declaration":
                                name_node = child.child_by_field_name("name")
                                if name_node:
                                    name = name_node.text.decode('utf8')
                                    functions[name] = {
                                        'start': child.start_byte,
                                        'end': node.end_byte
                                    }
                                    if self._debug:
                                        logger.debug(f"Added error recovery function: {name}")
                    
                    # Navigate down
                    if cursor.goto_first_child():
                        continue
                        
                    visited_children = True
                
                # Navigate sideways/up
                if cursor.goto_next_sibling():
                    visited_children = False
                else:
                    if not cursor.goto_parent():
                        break
                    visited_children = True
            
            return functions
            
        except Exception as e:
            logger.warning(f"Error in function extraction: {e}")
            return {}

    def _process_error_node(self, error_node: Node, functions: Dict[str, Dict[str, int]]) -> None:
        """Process error node to find function definitions."""
        try:
            # Get all children and siblings
            nodes_to_check = list(error_node.children)
            
            # Add siblings after error node
            current = error_node
            while current.next_sibling:
                nodes_to_check.append(current.next_sibling)
                current = current.next_sibling
            
            # Check each node
            for node in nodes_to_check:
                # Look for def keyword followed by a call node (error recovery case)
                if node.type == "def" and node.next_sibling and node.next_sibling.type == "call":
                    call_node = node.next_sibling
                    name_node = call_node.child_by_field_name("function") or call_node.children[0]
                    if name_node and name_node.type == "identifier":
                        try:
                            name = name_node.text.decode('utf8')
                            functions[name] = {
                                'start': name_node.start_byte,  # Use byte offsets
                                'end': call_node.end_byte  # Use byte offsets
                            }
                            logger.debug(f"Added error-recovery function: {name}")
                        except Exception as e:
                            logger.warning(f"Error processing error-recovery function: {e}")
                
                # Python-style function
                elif node.type == "function_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node and name_node.type == "identifier":
                        try:
                            name = name_node.text.decode('utf8')
                            functions[name] = {
                                'start': name_node.start_byte,  # Use byte offsets
                                'end': node.end_byte  # Use byte offsets
                            }
                            logger.debug(f"Added post-error function: {name}")
                        except Exception as e:
                            logger.warning(f"Error processing post-error function: {e}")
                
                # JavaScript/TypeScript style
                elif node.type in ["function_declaration", "method_definition"]:
                    name_node = node.child_by_field_name("name")
                    if name_node and name_node.type in ["identifier", "property_identifier"]:
                        try:
                            name = name_node.text.decode('utf8')
                            functions[name] = {
                                'start': name_node.start_byte,  # Use byte offsets
                                'end': node.end_byte  # Use byte offsets
                            }
                            logger.debug(f"Added post-error function: {name}")
                        except Exception as e:
                            logger.warning(f"Error processing post-error function: {e}")
                            
        except Exception as e:
            logger.warning(f"Error processing error node: {e}")

    def _fallback_function_extraction(self, root_node: Node) -> Dict[str, Dict[str, int]]:
        """Fallback method using traversal when query fails."""
        functions = {}
        cursor = root_node.walk()
        
        if self._debug:
            logger.debug("\nStarting fallback traversal:")
            
        try:
            while True:
                node = cursor.node
                
                # Check for function definitions
                if node.type == "function_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node and name_node.type == "identifier":
                        try:
                            name = name_node.text.decode('utf8')
                            functions[name] = {
                                'start': node.start_byte,
                                'end': node.end_byte
                            }
                            if self._debug:
                                logger.debug(f"Added function (fallback): {name}")
                        except Exception as e:
                            logger.warning(f"Error processing function name: {e}")
                
                # Navigate tree
                if cursor.goto_first_child():
                    continue
                    
                if cursor.goto_next_sibling():
                    continue
                    
                while True:
                    if not cursor.goto_parent():
                        return functions
                    if cursor.goto_next_sibling():
                        break
                    
        except Exception as e:
            logger.warning(f"Error in fallback traversal: {e}")
            
        return functions

    def _get_node_context(self, node: Node) -> Dict[str, Any]:
        """Get context information for a node."""
        context = {
            'line': node.start_point[0] + 1,
            'column': node.start_point[1],
            'type': node.type,
            'parent_type': node.parent.type if node.parent else None,
            'has_error': node.has_error,
            'is_missing': node.is_missing,
            'is_extra': getattr(node, 'is_extra', False)
        }
        
        # Get surrounding tokens for context
        if node.prev_sibling:
            context['prev_token'] = node.prev_sibling.text.decode('utf-8') if node.prev_sibling.text else None
        if node.next_sibling:
            context['next_token'] = node.next_sibling.text.decode('utf-8') if node.next_sibling.text else None
            
        return context

    def _is_valid_error_context(self, error_node: Node, name_node: Node) -> bool:
        """Check if an error node and name node form a valid function definition context."""
        # Check if the error node contains 'def' and is followed by the name
        try:
            if error_node.type != "ERROR":
                return False
                
            # Check if 'def' is present in the error node
            error_text = error_node.text.decode('utf-8')
            if 'def' not in error_text:
                return False
                
            # Check if the name node is in a reasonable position relative to 'def'
            def_pos = error_node.start_byte + error_text.index('def')
            name_pos = name_node.start_byte
            
            # Name should come after 'def' and be within a reasonable distance
            return def_pos < name_pos and (name_pos - def_pos) < 50
            
        except Exception as e:
            logger.warning(f"Error checking error context: {e}")
            return False

    def _get_tree_depth(self, node: Node) -> int:
        """Calculate AST depth."""
        if not node.children:
            return 1
        return 1 + max(self._get_tree_depth(child) for child in node.children)

    def _estimate_complexity(self, node: Node) -> int:
        """Estimate code complexity from AST."""
        complexity = 1
        for child in node.children:
            if child.type in ["if_statement", "for_statement", "while_statement"]:
                complexity += 1
            complexity += self._estimate_complexity(child)
        return complexity

    def _debug_print_ast(self, node: Node, level: int = 0) -> None:
        """Print AST structure for debugging."""
        if not self._debug:
            return
        
        indent = "  " * level
        print(f"{indent}{node.type}: {node.text.decode('utf8') if node.text else ''}")
        print(f"{indent}Start: {node.start_point}, End: {node.end_point}")
        print(f"{indent}Error: {node.has_error}, Missing: {node.is_missing}")
        
        for child in node.children:
            self._debug_print_ast(child, level + 1)

    def _traverse_for_functions(self, cursor: TreeCursor, functions: Dict[str, Dict[str, int]]) -> None:
        """Traverse AST using tree-sitter cursor to find functions, including in error states."""
        try:
            while True:
                current = cursor.node

                # Check for function definitions based on language
                if current.type in ["function_definition", "function_declaration", "method_definition"]:
                    name_node = current.child_by_field_name("name")
                    if name_node and name_node.type in ["identifier", "property_identifier"]:
                        try:
                            name = name_node.text.decode('utf8')
                            functions[name] = {
                                'start': name_node.start_point[0],
                                'end': current.end_point[0]
                            }
                            logger.debug(f"Added function: {name}")
                        except Exception as e:
                            logger.warning(f"Error processing function name: {e}")

                # Handle error recovery
                elif current.type == "ERROR":
                    # Look for function indicators in error node
                    for child in current.children:
                        # Python-style functions
                        if child.type == "def":
                            next_sibling = child.next_sibling
                            if next_sibling and next_sibling.type == "identifier":
                                try:
                                    name = next_sibling.text.decode('utf8')
                                    functions[name] = {
                                        'start': next_sibling.start_point[0],
                                        'end': current.end_point[0]
                                    }
                                    logger.debug(f"Added error function: {name}")
                                except Exception as e:
                                    logger.warning(f"Error processing function in error state: {e}")
                        # JavaScript/TypeScript style functions
                        elif child.type == "function":
                            for sibling in current.children:
                                if sibling.type == "identifier":
                                    try:
                                        name = sibling.text.decode('utf8')
                                        functions[name] = {
                                            'start': sibling.start_point[0],
                                            'end': current.end_point[0]
                                        }
                                        logger.debug(f"Added error function: {name}")
                                    except Exception as e:
                                        logger.warning(f"Error processing function in error state: {e}")

                # Traverse tree
                if cursor.goto_first_child():
                    continue

                if cursor.goto_next_sibling():
                    continue

                # No more siblings, go up until we can go to the next sibling
                while True:
                    if not cursor.goto_parent():
                        return  # We've reached the root, we're done
                    if cursor.goto_next_sibling():
                        break

        except Exception as e:
            logger.warning(f"Error during tree traversal: {e}")

    def _load_language(self, lang: str) -> TSLanguage:
        """Load a tree-sitter language module with version compatibility check."""
        try:
            # Get language config
            config = TREE_SITTER_LANGUAGES[lang]
            lib_name = config["lib"]
            
            # Import the language module dynamically
            try:
                module_name = lib_name.replace("-", "_")
                language_module = importlib.import_module(module_name)
                
                # Create language object
                try:
                    # Handle special cases for typescript/tsx
                    if lib_name == "tree-sitter-typescript":
                        # TypeScript module exposes language functions in a submodule
                        if lang == "typescript":
                            language = TSLanguage(language_module.language_typescript())
                        elif lang == "tsx":
                            language = TSLanguage(language_module.language_tsx())
                    else:
                        # Standard language modules
                        if "language_func" in config:
                            language_func = getattr(language_module, config["language_func"])
                            language = TSLanguage(language_func())
                        else:
                            language = TSLanguage(language_module.language())
                        
                    return language
                    
                except Exception as e:
                    raise ParserError(f"Failed to initialize language {lang}: {str(e)}")
                
            except ImportError as e:
                raise ParserError(
                    f"Failed to import {lib_name}. Please install with: pip install {lib_name}"
                )
                
        except Exception as e:
            if isinstance(e, ParserError):
                raise e
            raise ParserError(f"Failed to load language {lang}: {str(e)}")

    def _initialize_queries(self, lang: str) -> None:
        """Initialize queries for a language."""
        try:
            config = TREE_SITTER_LANGUAGES[lang]
            language = self._languages[lang]
            
            # Initialize function queries
            try:
                pattern = self._QUERY_PATTERNS.get(lang)
                if pattern:
                    self._queries[f"{lang}_functions"] = language.query(pattern)
                    logger.debug(f"Initialized {lang} function queries")
            except Exception as e:
                logger.warning(f"Failed to create function queries for {lang}: {e}")
                
            # Initialize class queries if needed
            if "class_query" in config:
                try:
                    self._queries[f"{lang}_classes"] = language.query(config["class_query"])
                    logger.debug(f"Initialized {lang} class queries")
                except Exception as e:
                    logger.warning(f"Failed to create class queries for {lang}: {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to initialize queries for {lang}: {e}")

    def _get_query_string(self, lang: str, query_name: str) -> Optional[str]:
        """Get query string from config or default location."""
        # First check if query is defined in config
        config = TREE_SITTER_LANGUAGES[lang]
        
        # Check for language-specific query
        if f"{query_name}_query" in config:
            return config[f"{query_name}_query"]
        
        if isinstance(config.get("queries", None), Dict):
            queries = config["queries"]
            if query_name in queries:
                return queries[query_name]
        
        # Default queries based on language
        if query_name == "functions":
            if lang in ["javascript", "typescript", "tsx"]:
                return """
                (function_declaration
                  name: (identifier) @function.def)
                (method_definition
                  name: (property_identifier) @function.def)
                """
            return """
            (function_definition
              name: (identifier) @function.def)
            """
        elif query_name == "classes":
            if lang in ["javascript", "typescript", "tsx"]:
                return """
                (class_declaration
                  name: (identifier) @class.def)
                """
            return """
            (class_definition
              name: (identifier) @class.def)
            """
        
        return None

    def _get_syntax_errors(self, node: Node) -> List[str]:
        """Get syntax errors from AST.
        
        Args:
            node: Root node of AST
            
        Returns:
            List of error messages
        """
        errors = []
        cursor = node.walk()
        
        try:
            while True:
                if cursor.node.has_error:
                    # Get error context
                    error_line = cursor.node.start_point[0] + 1
                    error_msg = f"Syntax error at line {error_line}"
                    if error_msg not in errors:  # Avoid duplicates
                        errors.append(error_msg)
                
                # Navigate tree
                if cursor.goto_first_child():
                    continue
                    
                if cursor.goto_next_sibling():
                    continue
                    
                while True:
                    if not cursor.goto_parent():
                        return errors
                    if cursor.goto_next_sibling():
                        break
                    
        except Exception as e:
            logger.warning(f"Error collecting syntax errors: {e}")
            
        return errors
