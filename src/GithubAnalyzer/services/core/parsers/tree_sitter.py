"""Tree-sitter parser implementation."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from tree_sitter import Language as TSLanguage, Parser as TSParser, Node, Tree, TreeCursor

from ....models.core.errors import ParserError, FileOperationError
from ....models.analysis.ast import ParseResult
from ....config.language_config import TREE_SITTER_LANGUAGES
from ....utils.file_utils import get_file_type, is_binary_file, validate_file_path
from ....utils.logging import get_logger
from .base import BaseParser

logger = get_logger(__name__)

class TreeSitterParser(BaseParser):
    """Parser implementation using tree-sitter."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self._languages: Dict[str, TSLanguage] = {}
        self._parsers: Dict[str, TSParser] = {}
        self._queries: Dict[str, Dict[str, Any]] = {}
        self._encoding = "utf8"
        self._timeout_micros = None
        self._included_ranges = None
        self.initialized = False

    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize tree-sitter parsers."""
        try:
            logger.info("Initializing tree-sitter parsers")
            languages = languages or ["python", "javascript", "typescript"]

            for lang in languages:
                try:
                    module_name = f"tree_sitter_{lang}"
                    try:
                        language_module = __import__(module_name)
                    except ImportError:
                        if lang not in TREE_SITTER_LANGUAGES:
                            raise ParserError(f"Language {lang} not supported")
                        raise ParserError(f"Language {lang} not installed. Run: pip install {module_name}")

                    # Handle special cases for different languages
                    try:
                        # TypeScript: Has both TS and TSX
                        if lang == "typescript":
                            ts_language = TSLanguage(language_module.language_typescript())
                            tsx_language = TSLanguage(language_module.language_tsx())
                            
                            ts_parser = TSParser()
                            tsx_parser = TSParser()
                            
                            ts_parser.language = ts_language
                            tsx_parser.language = tsx_language
                            
                            self._languages[lang] = ts_language
                            self._languages["tsx"] = tsx_language
                            self._parsers[lang] = ts_parser
                            self._parsers["tsx"] = tsx_parser
                            continue

                        # JavaScript handles JSX natively
                        elif lang == "javascript":
                            language = TSLanguage(language_module.language())
                            parser = TSParser()
                            parser.language = language
                            self._languages[lang] = language
                            self._parsers[lang] = parser
                            continue

                        # PHP: Requires get_language() call
                        elif lang == "php":
                            language = TSLanguage(language_module.get_language())
                            parser = TSParser()
                            parser.language = language
                            self._languages[lang] = language
                            self._parsers[lang] = parser
                            continue

                        # Ruby: May have embedded languages
                        elif lang == "ruby":
                            language = TSLanguage(language_module.get_parser())
                            parser = TSParser()
                            parser.language = language
                            self._languages[lang] = language
                            self._parsers[lang] = parser
                            continue

                    except AttributeError as e:
                        # Try standard initialization if special case fails
                        logger.debug(f"Special initialization failed for {lang}, trying standard: {e}")
                        language = TSLanguage(language_module.language())
                        parser = TSParser()
                        parser.language = language
                        self._languages[lang] = language
                        self._parsers[lang] = parser
                        continue

                    # Standard language initialization
                    language = TSLanguage(language_module.language())
                    parser = TSParser()
                    parser.language = language
                    
                    self._languages[lang] = language
                    self._parsers[lang] = parser

                except Exception as e:
                    raise ParserError(f"Failed to initialize language {lang}: {str(e)}")

            self.initialized = True
            logger.info("Tree-sitter parsers initialized successfully")
        except Exception as e:
            raise ParserError(f"Failed to initialize parser: {str(e)}")

    def parse(self, content: str, language: str) -> ParseResult:
        """Parse source code content."""
        if not self.initialized:
            raise ParserError("Parser not initialized")

        if language not in self._parsers:
            raise ParserError(f"Language {language} not supported")

        try:
            # Parse content
            parser = self._parsers[language]
            tree = parser.parse(bytes(content, self._encoding))
            
            # Initialize metadata
            metadata = {
                "encoding": self._encoding,
                "raw_content": content,
                "root_type": tree.root_node.type,
                "analysis": {
                    "functions": {},  # Initialize empty dict for functions
                    "errors": self._get_errors(tree.root_node)  # Use _get_errors directly
                }
            }

            # Extract functions even if there are errors
            if tree.root_node:
                functions = self._get_functions(tree.root_node, language)
                metadata["analysis"]["functions"] = functions

            return ParseResult(
                ast=tree,
                is_valid=not tree.root_node.has_error,
                node_count=tree.root_node.descendant_count,
                errors=self._get_errors(tree.root_node),  # This is fine as it's part of ParseResult
                metadata=metadata
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

    def _get_functions(self, node: Node, language: str) -> Dict[str, Dict[str, int]]:
        """Extract function definitions from AST."""
        functions = {}
        
        # Use cursor for reliable traversal, even through error nodes
        cursor = node.walk()
        
        def visit(cursor: TreeCursor) -> None:
            logger.debug("Visiting node: %s at line %d", 
                        cursor.node.type, cursor.node.start_point[0])
            
            # Skip error nodes but continue traversal
            if cursor.node.type == "ERROR":
                logger.debug("Found ERROR node, attempting to continue traversal")
                if cursor.goto_next_sibling():
                    visit(cursor)
                return
            
            # Handle nodes that contain errors but might have valid children
            if cursor.node.has_error:
                # Still try to process this node if it looks like a function
                if (language == "python" and cursor.node.type == "function_definition"):
                    logger.debug("Processing function node with errors: %s", cursor.node.type)
                    process_function_node(cursor.node)
            
            # Language-specific function patterns
            if (
                # Python
                (language == "python" and (
                    cursor.node.type == "function_definition" or
                    (cursor.node.type == "def" and cursor.node.next_sibling and 
                     cursor.node.next_sibling.type == "identifier")
                )) or
                # JavaScript/TypeScript
                (language in ["javascript", "typescript"] and
                    cursor.node.type in ["function_declaration", "function", "method_definition"])
            ):
                logger.debug("Found potential function node: %s", cursor.node.type)
                process_function_node(cursor.node)
            
            def process_function_node(node: Node) -> None:
                """Process a potential function node, even if it contains errors."""
                name_node = (node.child_by_field_name("name") or 
                           (node.type == "def" and node.next_sibling))
                
                if name_node and name_node.type == "identifier":
                    functions[name_node.text.decode('utf8')] = {
                        'start': node.start_point[0],
                        'end': node.end_point[0]
                    }
            
            # Continue traversal even after errors
            if cursor.goto_first_child():
                visit(cursor)
                cursor.goto_parent()
            
            if cursor.goto_next_sibling():
                visit(cursor)

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
