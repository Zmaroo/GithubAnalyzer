"""Tree-sitter parser implementation."""

import importlib
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from tree_sitter import Language, Node, Parser, Query, Tree, TreeCursor

from GithubAnalyzer.models.core.errors import ParseError
from GithubAnalyzer.models.core.parse import ParseResult
from GithubAnalyzer.utils.logging import setup_logger

from .base import BaseParser

logger = setup_logger(__name__)


def is_binary_string(bytes_data: bytes, sample_size: int = 1024) -> bool:
    """Check if a byte string appears to be binary.

    Args:
        bytes_data: The bytes to check
        sample_size: Number of bytes to check

    Returns:
        True if the data appears to be binary
    """
    # Check for null bytes which indicate binary data
    if b"\x00" in bytes_data[:sample_size]:
        return True

    # Try decoding as UTF-8
    try:
        bytes_data[:sample_size].decode("utf-8")
        return False
    except UnicodeDecodeError:
        return True


class TreeSitterParser(BaseParser):
    """Parser implementation using tree-sitter."""

    SUPPORTED_LANGUAGES = {
        # Core languages
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "java": ".java",
        "cpp": ".cpp",
        "c": ".c",
        "rust": ".rs",
        "go": ".go",
        "ruby": ".rb",
        # Web languages
        "html": ".html",
        "css": ".css",
        "json": ".json",
        "yaml": ".yaml",
        # Shell languages
        "bash": ".sh",
        # Additional languages
        "php": ".php",
        "csharp": ".cs",
        "scala": ".scala",
        "kotlin": ".kt",
        "lua": ".lua",
        "toml": ".toml",
        "xml": ".xml",
        "markdown": ".md",
        "sql": ".sql",
        "arduino": ".ino",
        "cmake": "CMakeLists.txt",
        "cuda": ".cu",
        "groovy": ".groovy",
        "matlab": ".m",
    }

    # Query patterns for finding functions in different languages
    QUERY_PATTERNS = {
        "python": """
            (function_definition
              name: (identifier) @function_name)
        """,
        "javascript": """
            (function_declaration
              name: (identifier) @function_name)
            (method_definition
              name: (property_identifier) @function_name)
            (arrow_function
              name: (identifier) @function_name)
            (variable_declarator
              name: (identifier) @function_name
              value: (function_expression))
            (variable_declarator
              name: (identifier) @function_name
              value: (arrow_function))
        """,
        "java": """
            (method_declaration
              name: (identifier) @function_name)
        """,
        "cpp": """
            (function_definition
              declarator: (function_declarator
                declarator: (identifier) @function_name))
        """,
        "rust": """
            (function_item
              name: (identifier) @function_name)
        """,
        "go": """
            (function_declaration
              name: (identifier) @function_name)
        """,
    }

    def __init__(self, timeout_micros: Optional[int] = None) -> None:
        """Initialize the parser.

        Args:
            timeout_micros: Optional timeout in microseconds for parsing operations
        """
        self._languages: Dict[str, Any] = {}
        self._parsers: Dict[str, Parser] = {}
        self._queries: Dict[str, Query] = {}
        self._encoding = "utf8"  # Always use UTF-8 as recommended
        self._timeout_micros = timeout_micros
        self._included_ranges = None
        self.initialized = False
        self._logger = logging.getLogger(__name__)
        self._logger.info("Initializing tree-sitter parsers")

    def __del__(self) -> None:
        """Clean up parser resources."""
        self.cleanup()

    def set_encoding(self, encoding: str) -> None:
        """Set the encoding to use for parsing.

        Args:
            encoding: The encoding to use (must be 'utf8')
        """
        if encoding.lower() != "utf8":
            logger.warning(
                "Only UTF-8 encoding is supported, ignoring request for %s", encoding
            )
        self._encoding = "utf8"

    def set_timeout(self, timeout_micros: Optional[int]) -> None:
        """Set the parsing timeout in microseconds."""
        self._timeout_micros = timeout_micros
        for parser in self._parsers.values():
            parser.timeout_micros = timeout_micros

    def set_included_ranges(self, ranges: Optional[List[tuple]]) -> None:
        """Set the ranges of text that the parser will include when parsing."""
        self._included_ranges = ranges
        for parser in self._parsers.values():
            parser.included_ranges = ranges

    def enable_debug_graphs(self, file_path: Optional[Union[str, Path]]) -> None:
        """Enable or disable debug graph output.

        Args:
            file_path: Path to write DOT graphs to, or None to disable
        """
        file_obj = None
        if file_path:
            file_obj = open(file_path, "w")
        for parser in self._parsers.values():
            parser.print_dot_graphs(file_obj)

    def _get_language_for_file(self, file_path: Union[str, Path]) -> Optional[str]:
        """Get language for file based on extension.

        Args:
            file_path: Path to the file.

        Returns:
            Language identifier if found, None otherwise.
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        name = file_path.name

        # First check exact filename matches (e.g. CMakeLists.txt)
        for lang, pattern in self.SUPPORTED_LANGUAGES.items():
            if pattern == name:
                return lang

        # Then check extensions
        for lang, pattern in self.SUPPORTED_LANGUAGES.items():
            if pattern == extension:
                return lang

        return None

    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize tree-sitter parsers."""
        logger.info("Initializing tree-sitter parsers")
        self._parsers = {}
        self._languages = {}
        self._queries = {}

        if languages is None:
            languages = list(self.SUPPORTED_LANGUAGES.keys())

        loaded_languages = []
        for lang in languages:
            logger.info("Loading language: %s", lang)
            try:
                if lang not in self.SUPPORTED_LANGUAGES:
                    logger.warning("Language %s not supported", lang)
                    continue

                # Import the language module
                module_name = f"tree_sitter_{lang}"
                try:
                    module = importlib.import_module(module_name)
                    if not hasattr(module, "language"):
                        logger.warning(
                            "Language module %s has no language() function", module_name
                        )
                        continue
                except ImportError:
                    logger.warning("Language module not found: %s", module_name)
                    continue

                # Get language from module
                language = Language(module.language())

                # Create parser with configuration
                parser = Parser()
                parser.language = language
                if self._timeout_micros is not None:
                    parser.timeout_micros = self._timeout_micros
                if self._included_ranges is not None:
                    parser.included_ranges = self._included_ranges

                # Initialize query for the language if pattern exists
                if lang in self.QUERY_PATTERNS:
                    try:
                        self._queries[lang] = language.query(self.QUERY_PATTERNS[lang])
                    except Exception as e:
                        logger.warning(
                            "Failed to create query for language %s: %s", lang, str(e)
                        )

                self._languages[lang] = language
                self._parsers[lang] = parser
                loaded_languages.append(lang)
            except Exception as e:
                logger.warning("Failed to set language %s: %s", lang, str(e))

        if not loaded_languages:
            raise ParseError(
                "No languages could be loaded. Please ensure language packages are installed."
            )

        self.initialized = True

    def parse(self, code: str, language: str) -> ParseResult:
        """Parse code using tree-sitter.

        Args:
            code: The source code to parse.
            language: The programming language of the code.

        Returns:
            ParseResult object containing parse results

        Raises:
            ParseError: If language is not supported or parsing fails
        """
        if not self.initialized:
            self.initialize()

        if language not in self._parsers:
            raise ParseError(f"Language {language} not supported")

        try:
            # Convert code to bytes only once
            code_bytes = bytes(code, "utf8")

            # Check if binary
            if is_binary_string(code_bytes):
                return ParseResult(
                    ast=None,
                    language=language,
                    is_valid=False,
                    line_count=0,
                    node_count=0,
                    errors=["File appears to be binary (not a text file)"],
                    metadata={"encoding": "utf8"},
                )

            parser = self._parsers[language]

            # Parse with timeout
            start_time = time.time()
            tree = parser.parse(code_bytes)
            parse_time = time.time() - start_time

            # Count lines and nodes
            line_count = len(code.splitlines())
            node_count = self._count_nodes(tree.root_node)

            # Get error messages
            errors = self._check_node_for_errors(tree.root_node)

            # Check if the tree is valid
            is_valid = not (
                tree.root_node.type == "ERROR"
                or tree.root_node.has_error
                or any(
                    child.type == "ERROR" or child.has_error
                    for child in tree.root_node.children
                )
                or len(errors) > 0
            )

            # Find functions using Tree-sitter's query system
            functions = []
            if language in self._queries:
                try:
                    query = self._queries[language]
                    matches = query.matches(tree.root_node)
                    for match in matches:
                        pattern_index, captures = match
                        for capture_name, node in captures:
                            if capture_name == "function_name" and not node.has_error:
                                name = node.text.decode("utf8")
                                if name not in functions:
                                    functions.append(name)
                except Exception as e:
                    self._logger.warning(f"Query failed: {e}")

            # If query failed or no functions found, try cursor-based approach
            if not functions:
                functions = self._find_functions(tree)

            # Build metadata
            metadata = {
                "raw_content": code,
                "analysis": {"errors": errors, "warnings": [], "functions": functions},
                "root_type": tree.root_node.type,
                "encoding": "utf8",
                "parse_time": parse_time,
                "language": language,
                "has_errors": not is_valid,
            }

            return ParseResult(
                ast=tree,
                language=language,
                is_valid=is_valid,
                line_count=line_count,
                node_count=node_count,
                errors=errors,
                metadata=metadata,
            )
        except Exception as e:
            return ParseResult(
                ast=None,
                language=language,
                is_valid=False,
                line_count=0,
                node_count=0,
                errors=[f"Failed to parse {language} code: {str(e)}"],
                metadata={"encoding": "utf8"},
            )

    def parse_file(self, file_path: str) -> ParseResult:
        """Parse a file using tree-sitter.

        Args:
            file_path: Path to the file to parse.

        Returns:
            ParseResult object containing parse results

        Raises:
            ParseError: If file cannot be read or parsed.
        """
        try:
            with open(file_path, "rb") as f:
                code_bytes = f.read()

            # Check if binary
            if is_binary_string(code_bytes):
                raise ParseError(f"File {file_path} is not a text file")

            code = code_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ParseError(f"File {file_path} is not a valid UTF-8 text file")
        except Exception as e:
            raise ParseError(f"Failed to read file {file_path}: {str(e)}")

        language = self._get_language_for_file(file_path)
        if not language:
            raise ParseError(f"Unsupported file extension: {Path(file_path).suffix}")

        return self.parse(code, language)

    def cleanup(self) -> None:
        """Clean up parser resources explicitly."""
        for parser in self._parsers.values():
            parser.reset()
        self._parsers.clear()
        self._queries.clear()
        self._languages.clear()
        self.initialized = False

    def _find_functions(self, tree: Tree) -> List[str]:
        """Find all function names in the tree, including those in partially valid code."""
        functions = []
        cursor = tree.walk()
        visited_children = False

        while True:
            if not visited_children:
                node = cursor.node

                # Check if this is a function definition
                if node.type == "function_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        name = name_node.text.decode("utf8")
                        if name not in functions:
                            functions.append(name)

                # Check for function-like structures in error nodes
                elif node.type == "ERROR":
                    # First check for nodes with field names
                    for child in node.children:
                        if (
                            child.type == "identifier"
                            and child.prev_sibling
                            and child.prev_sibling.type == "def"
                        ):
                            name = child.text.decode("utf8")
                            if name not in functions:
                                functions.append(name)
                        elif (
                            child.type == "call"
                            and child.children
                            and child.prev_sibling
                            and child.prev_sibling.type == "def"
                        ):
                            call_id = child.children[0]
                            if call_id.type == "identifier":
                                name = call_id.text.decode("utf8")
                                if name not in functions:
                                    functions.append(name)

                    # Then check the text content for any missed function definitions
                    text = node.text.decode("utf8")
                    lines = text.split("\n")
                    for line in lines:
                        line = line.strip()
                        if line.startswith("def "):
                            # Extract everything between 'def ' and the first '(' or ':'
                            name = line[4:].strip()
                            for delim in ["(", ":"]:
                                if delim in name:
                                    name = name.split(delim)[0].strip()
                                    break
                            if name and name not in functions:
                                functions.append(name)

                if not cursor.goto_first_child():
                    visited_children = True
            elif cursor.goto_next_sibling():
                visited_children = False
            elif not cursor.goto_parent():
                break

        return functions

    def _get_parser(self, language: str) -> Parser:
        """Get parser for the specified language.

        Args:
            language: Language identifier.

        Returns:
            Parser instance.

        Raises:
            ParseError: If parser is not initialized or language not supported.
        """
        if not self.initialized:
            raise ParseError("Parser not initialized")

        if language not in self._languages:
            raise ParseError(f"Language {language} not supported")

        if language not in self._parsers:
            raise ParseError(f"Parser for {language} not initialized")

        return self._parsers[language]

    def _count_nodes(self, node: Node) -> int:
        """Count nodes in the AST using Tree-sitter's cursor.

        Args:
            node: The root node to start counting from.

        Returns:
            Total number of nodes in the tree.
        """
        cursor = node.walk()
        count = 0
        visited_children = False

        while True:
            if not visited_children:
                count += 1
                if not cursor.goto_first_child():
                    visited_children = True
            elif cursor.goto_next_sibling():
                visited_children = False
            elif not cursor.goto_parent():
                break

        return count

    def _check_node_for_errors(self, node: Node) -> List[str]:
        """Check a node and its children for errors using Tree-sitter's API.

        Args:
            node: The root node to check for errors.

        Returns:
            List of error messages found in the tree.
        """
        errors = []

        def visit_node(node: Node) -> None:
            """Visit a node and its children."""
            # Check for ERROR nodes and nodes with errors
            if node.type == "ERROR" or node.has_error:
                start_point = node.start_point
                error_msg = (
                    f"Syntax error at line {start_point[0] + 1}, "
                    f"column {start_point[1] + 1}"
                )

                # Check specific error cases
                if node.parent and node.parent.type == "function_definition":
                    if "(" not in node.text.decode("utf8"):
                        error_msg += ": Missing parenthesis in function definition"
                    else:
                        error_msg += ": Invalid function definition"
                else:
                    error_msg += ": Invalid syntax"

                errors.append(error_msg)

            # Check for indentation errors in blocks
            if (
                node.type == "block"
                and node.parent
                and node.parent.type == "function_definition"
            ):
                if node.children:
                    # Get the first non-whitespace child
                    first_stmt = None
                    for child in node.children:
                        if child.type not in ["comment", "newline"]:
                            first_stmt = child
                            break

                    if (
                        first_stmt
                        and first_stmt.start_point[1] <= node.parent.start_point[1]
                    ):
                        start_point = first_stmt.start_point
                        errors.append(
                            f"Syntax error at line {start_point[0] + 1}, "
                            f"column {start_point[1] + 1}: Invalid indentation"
                        )

            # Check for unclosed strings
            if node.type == "string" or node.type == "ERROR":
                text = node.text.decode("utf8")
                if text.count('"') % 2 == 1 or text.count("'") % 2 == 1:
                    start_point = node.start_point
                    errors.append(
                        f"Syntax error at line {start_point[0] + 1}, "
                        f"column {start_point[1] + 1}: Unclosed string literal"
                    )

            # Visit all named children first (more likely to contain errors)
            for child in node.named_children:
                visit_node(child)

            # Then visit any remaining children
            for child in node.children:
                if child not in node.named_children:
                    visit_node(child)

        # Start traversal from the root
        visit_node(node)
        return errors
