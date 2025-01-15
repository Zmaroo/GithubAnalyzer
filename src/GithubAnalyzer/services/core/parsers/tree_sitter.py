"""Tree-sitter parser implementation."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from tree_sitter import Language, Node, Parser as TSParser, Tree, TreeCursor

from ....models.analysis.ast import ParseResult
from ....models.core.errors import ParserError
from ....config.language_config import (
    TREE_SITTER_LANGUAGES,
    get_language_variant,
)
from ....utils.file_utils import get_file_type, is_binary_file, validate_file_path
from ....utils.logging import get_logger, configure_logging
from .base import BaseParser

# Configure application-level logging
configure_logging()
logger = get_logger("GithubAnalyzer.parsers.tree_sitter")

class TreeSitterParser(BaseParser):
    """Parser implementation using tree-sitter."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self._languages: Dict[str, Language] = {}
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
            languages = languages or list(TREE_SITTER_LANGUAGES.keys())
            
            for lang in languages:
                if lang not in TREE_SITTER_LANGUAGES:
                    raise ParserError(f"Language {lang} not supported")
                try:
                    # Get module name and variant
                    module_name, variant = get_language_variant(lang)
                    
                    # Use tree-sitter's built-in language loading
                    language_module = __import__(module_name)
                    
                    # Create parser
                    parser = TSParser()
                    if variant:
                        language = Language(language_module.language(), variant)
                    else:
                        language = Language(language_module.language())
                    parser.language = language
                    
                    self._languages[lang] = language
                    self._parsers[lang] = parser
                except ImportError:
                    raise ParserError(f"Language {lang} not installed. Run: pip install {module_name}")
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
        """Parse a source code file.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            ParseResult containing AST and metadata
            
        Raises:
            ParserError: If parsing fails
        """
        try:
            path = validate_file_path(file_path)
            if not path.exists():
                raise ParserError(f"File not found: {path}")
                
            if is_binary_file(str(path)):
                raise ParserError(f"File {path} is not a text file")
                
            language = self._get_language_for_file(path)
            if not language:
                raise ParserError(f"Unsupported file extension: {path.suffix}")
                
            with open(path, 'r', encoding=self._encoding) as f:
                content = f.read()
                
            result = self.parse(content, language)
            result.metadata["file_path"] = str(path)
            return result
        except Exception as e:
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
        return {
            "functions": self._get_functions(tree.root_node, language),
            "errors": self._get_syntax_errors(tree.root_node),
            "metrics": {
                "depth": self._get_tree_depth(tree.root_node),
                "complexity": self._estimate_complexity(tree.root_node),
            }
        }

    def _get_functions(self, node: Node, language: str) -> Dict[str, Any]:
        """Extract function information from AST."""
        functions = {}
        if language == "python" and node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                functions[name_node.text.decode(self._encoding)] = {
                    "start": node.start_point[0],
                    "end": node.end_point[0],
                }
        for child in node.children:
            functions.update(self._get_functions(child, language))
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
