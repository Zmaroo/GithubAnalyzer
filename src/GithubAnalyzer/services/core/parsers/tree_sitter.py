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
        """Initialize tree-sitter parsers.
        
        Args:
            languages: Optional list of languages to initialize support for
            
        Raises:
            ParserError: If initialization fails
        """
        try:
            logger.info("Initializing tree-sitter parsers")
            # Start with core languages if none specified
            languages = languages or ["python", "javascript", "typescript"]
            
            for lang in languages:
                try:
                    # Try to import the language module first
                    module_name = f"tree_sitter_{lang}"
                    try:
                        language_module = __import__(module_name)
                    except ImportError:
                        if lang not in TREE_SITTER_LANGUAGES:
                            raise ParserError(f"Language {lang} not supported")
                        raise ParserError(f"Language {lang} not installed. Run: pip install {module_name}")

                    # Handle TypeScript special case
                    if lang == "typescript":
                        try:
                            # Get both TS and TSX parsers from typescript module
                            ts_language = TSLanguage(language_module.language_typescript())
                            tsx_language = TSLanguage(language_module.language_tsx())
                            
                            # Create parsers for both
                            ts_parser = TSParser()
                            tsx_parser = TSParser()
                            
                            ts_parser.language = ts_language
                            tsx_parser.language = tsx_language
                            
                            self._languages[lang] = ts_language
                            self._languages["tsx"] = tsx_language
                            self._parsers[lang] = ts_parser
                            self._parsers["tsx"] = tsx_parser
                            continue
                        except AttributeError:
                            raise ParserError("Failed to initialize TypeScript: no valid language loader found")
                    
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
        """Parse source code content.
        
        Args:
            content: Source code to parse
            language: Programming language of the content
            
        Returns:
            ParseResult containing AST and metadata
            
        Raises:
            ParserError: If parsing fails
        """
        if not self.initialized:
            raise ParserError("Parser not initialized")
            
        if language not in self._parsers:
            raise ParserError(f"Language {language} not supported")
            
        try:
            tree = self._parsers[language].parse(
                bytes(content, self._encoding)
            )
            
            is_valid = not tree.root_node.has_error
            errors = self._get_syntax_errors(tree.root_node) if not is_valid else []
            
            return ParseResult(
                ast=tree,
                language=language,
                is_valid=is_valid,
                line_count=len(content.splitlines()),
                node_count=self._count_nodes(tree.root_node),
                errors=errors,
                metadata={
                    "encoding": self._encoding,
                    "raw_content": content,
                    "root_type": tree.root_node.type,
                    "analysis": self._analyze_tree(tree, language),
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

    def _get_syntax_errors(self, node: Node) -> List[str]:
        """Get syntax errors from AST."""
        errors = []
        if node.has_error:
            errors.append(f"Syntax error at line {node.start_point[0] + 1}")
        for child in node.children:
            errors.extend(self._get_syntax_errors(child))
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
            # Check for both explicit function_definition and potential function patterns
            if (cursor.node.type == "function_definition" or
                (cursor.node.type == "def" and cursor.node.next_sibling and 
                 cursor.node.next_sibling.type == "identifier")):
                
                # Get function name, handling both normal and error cases
                name_node = (cursor.node.child_by_field_name("name") or 
                            (cursor.node.type == "def" and cursor.node.next_sibling))
                
                if name_node and name_node.type == "identifier":
                    functions[name_node.text.decode('utf8')] = {
                        'start': cursor.node.start_point[0],
                        'end': cursor.node.end_point[0]
                    }
            
            # Continue traversal
            if cursor.goto_first_child():
                visit(cursor)
                cursor.goto_parent()
            
            if cursor.goto_next_sibling():
                visit(cursor)
        
        try:
            visit(cursor)
        except Exception as e:
            logger.debug(f"Error during tree traversal: {e}")
            # Fall back to simple traversal if cursor fails
            for child in node.children:
                child_functions = self._get_functions(child, language)
                functions.update(child_functions)
        
        return functions

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
