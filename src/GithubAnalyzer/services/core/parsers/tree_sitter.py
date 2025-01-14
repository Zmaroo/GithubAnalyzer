"""Tree-sitter parser implementation."""

import importlib
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from tree_sitter import Language, Node, Parser, Query, Tree, TreeCursor

from ....models.core.errors import ParseError
from ....models.core.parse import ParseResult
from ....utils.logging import setup_logger
from .base import BaseParser

logger = setup_logger(__name__)


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
              name: (identifier) @function.def
              parameters: (parameters) @function.params
              body: (block) @function.body)
            (class_definition
              name: (identifier) @class.def
              body: (block) @class.body)
            (import_statement
              name: (dotted_name) @import.module)
            (call
              function: (identifier) @function.call)
        """,
        "javascript": """
            (function_declaration
              name: (identifier) @function.def
              body: (statement_block) @function.body)
            (method_definition
              name: (property_identifier) @function.def
              body: (statement_block) @function.body)
            (class_declaration
              name: (identifier) @class.def
              body: (class_body) @class.body)
            (arrow_function
              parameters: (formal_parameters) @function.params
              body: [(statement_block) (expression)] @function.body)
            (import_statement
              source: (string) @import.module)
        """,
        "java": """
            (method_declaration
              name: (identifier) @function.def
              parameters: (formal_parameters) @function.params
              body: (block) @function.body)
            (class_declaration
              name: (identifier) @class.def
              body: (class_body) @class.body)
            (import_declaration
              name: (identifier) @import.module)
        """,
        "cpp": """
            (function_definition
              declarator: (function_declarator
                declarator: (identifier) @function.def)
              body: (compound_statement) @function.body)
            (class_specifier
              name: (type_identifier) @class.def
              body: (field_declaration_list) @class.body)
            (namespace_definition
              name: (identifier) @namespace.def
              body: (declaration_list) @namespace.body)
        """,
        "rust": """
            (function_item
              name: (identifier) @function.def
              parameters: (parameters) @function.params
              body: (block) @function.body)
            (impl_item
              trait: (type_identifier) @impl.trait
              type: (type_identifier) @impl.type)
            (mod_item
              name: (identifier) @module.def)
        """,
        "go": """
            (function_declaration
              name: (identifier) @function.def
              parameters: (parameter_list) @function.params
              result: (result_list)? @function.return
              body: (block) @function.body)
            (method_declaration
              receiver: (parameter_list) @method.receiver
              name: (field_identifier) @method.def
              body: (block) @method.body)
            (import_spec
              path: (interpreted_string_literal) @import.module)
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
        self._query_cache: Dict[str, Dict[str, List[Node]]] = (
            {}
        )  # language -> pattern_type -> nodes
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

    def _count_nodes(self, node: Node) -> int:
        """Count nodes in the AST recursively."""
        count = 1  # Count current node
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def _traverse_tree_cursor(
        self, cursor: TreeCursor, visit_fn: Callable[[Node], None]
    ) -> None:
        """Traverse the tree using Tree-sitter's cursor API efficiently."""
        while True:
            visit_fn(cursor.node)

            if cursor.goto_first_child():
                continue

            if cursor.goto_next_sibling():
                continue

            retracing = True
            while retracing:
                if not cursor.goto_parent():
                    return
                if cursor.goto_next_sibling():
                    retracing = False
                    break

    def _find_nodes_by_type(self, node: Node, node_type: str) -> List[Node]:
        """Find all nodes of a specific type using efficient cursor traversal."""
        nodes = []
        cursor = node.walk()

        def visit(node: Node) -> None:
            if node.is_named and node.type == node_type:
                if not node.has_error:
                    nodes.append(node)
                elif node.parent:
                    # Add context about the error location
                    field_name = node.parent.field_name_for_child(node.id)
                    self._logger.debug(
                        f"Found error node of type {node_type} in field {field_name}"
                    )

        self._traverse_tree_cursor(cursor, visit)
        return nodes

    def _find_error_nodes(self, node: Node) -> List[str]:
        """Find error nodes in the AST using Tree-sitter's cursor methods.

        Uses byte offsets for precise source mapping.
        """
        errors = []
        cursor = node.walk()

        def check_node(node: Node) -> None:
            # Check for explicit syntax errors
            if node.type == "ERROR":
                start_byte, end_byte = node.start_byte, node.end_byte
                start_point = node.start_point
                errors.append(
                    f"Syntax error at line {start_point[0] + 1}, "
                    f"column {start_point[1] + 1} "
                    f"(bytes {start_byte}-{end_byte}): Invalid syntax"
                )
                return

            # Check for nodes containing errors
            if node.has_error:
                start_byte, end_byte = node.start_byte, node.end_byte
                start_point = node.start_point
                errors.append(
                    f"Syntax error at line {start_point[0] + 1}, "
                    f"column {start_point[1] + 1} "
                    f"(bytes {start_byte}-{end_byte}): Invalid {node.type}"
                )

            # Special checks for function definitions
            if node.type == "function_definition":
                params = node.child_by_field_name("parameters")
                body = node.child_by_field_name("body")

                if not params or params.type == "ERROR":
                    start_byte, end_byte = node.start_byte, node.end_byte
                    start_point = node.start_point
                    errors.append(
                        f"Syntax error at line {start_point[0] + 1}, "
                        f"column {start_point[1] + 1} "
                        f"(bytes {start_byte}-{end_byte}): Missing or invalid function parameters"
                    )

                if not body or body.type == "ERROR":
                    start_byte, end_byte = node.start_byte, node.end_byte
                    start_point = node.start_point
                    errors.append(
                        f"Syntax error at line {start_point[0] + 1}, "
                        f"column {start_point[1] + 1} "
                        f"(bytes {start_byte}-{end_byte}): Missing or invalid function body"
                    )

                # Check indentation
                if body and body.named_children:
                    first_child = body.named_children[0]
                    if first_child.start_point[1] <= node.start_point[1]:
                        start_byte, end_byte = (
                            first_child.start_byte,
                            first_child.end_byte,
                        )
                        start_point = first_child.start_point
                        errors.append(
                            f"Syntax error at line {start_point[0] + 1}, "
                            f"column {start_point[1] + 1} "
                            f"(bytes {start_byte}-{end_byte}): Invalid indentation"
                        )

        # Use Tree-sitter's cursor methods for traversal
        while True:
            check_node(cursor.node)

            if cursor.goto_first_child():
                continue

            if cursor.goto_next_sibling():
                continue

            while not cursor.goto_next_sibling():
                if not cursor.goto_parent():
                    return errors

        return errors

    def _find_nodes_by_query(
        self, query: Query, tree: Tree, pattern_type: str, language: str
    ) -> List[Node]:
        """Find nodes in the tree that match the given query pattern type."""
        # Check cache first
        cache_key = f"{tree.root_node.id}:{pattern_type}"
        if language in self._query_cache and cache_key in self._query_cache[language]:
            return self._query_cache[language][cache_key]

        nodes = []
        try:
            # Set limits to prevent hanging
            query.set_match_limit(100)  # Limit in-progress matches
            query.set_timeout_micros(1000000)  # 1 second timeout

            # Get matches using Tree-sitter's built-in matches() method
            matches = query.matches(tree.root_node)
            for match in matches:
                for capture in match.captures:
                    if capture.name == pattern_type and not capture.node.has_error:
                        nodes.append(capture.node)

            # Cache the results
            if language not in self._query_cache:
                self._query_cache[language] = {}
            self._query_cache[language][cache_key] = nodes

        except Exception as e:
            self._logger.warning(f"Error executing query: {str(e)}")

        return nodes

    def _check_node_for_errors(self, node: Node) -> List[str]:
        """Check nodes for errors with enhanced context."""
        errors = []
        cursor = node.walk()

        def visit(node: Node) -> None:
            if node.type == "ERROR" or node.has_error:
                start_point = node.start_point
                error_msg = (
                    f"Syntax error at line {start_point[0] + 1}, "
                    f"column {start_point[1] + 1} "
                    f"(bytes {node.start_byte}-{node.end_byte})"
                )

                # Enhanced context using parent relationship
                if node.parent and node.parent.is_named:
                    # Find the field name by checking each child
                    field_name = None
                    for child in node.parent.children:
                        if child.id == node.id:
                            field_name = node.parent.field_name_for_child(
                                node.parent.children.index(child)
                            )
                            break

                    error_msg += (
                        f": Invalid {field_name or node.type} in {node.parent.type}"
                    )
                else:
                    error_msg += f": Invalid {node.type}"

                errors.append(error_msg)

            # Check indentation using parent context
            if node.is_named and node.type == "block":
                if node.parent and node.parent.is_named:
                    # Find the field name by checking each child
                    field_name = None
                    for child in node.parent.children:
                        if child.id == node.id:
                            field_name = node.parent.field_name_for_child(
                                node.parent.children.index(child)
                            )
                            break

                    if field_name == "body":
                        first_child = next(
                            (
                                c
                                for c in node.named_children
                                if c.type not in ["comment", "newline"]
                            ),
                            None,
                        )
                        if (
                            first_child
                            and first_child.start_point[1] <= node.parent.start_point[1]
                        ):
                            errors.append(
                                f"Indentation error at line {first_child.start_point[0] + 1}, "
                                f"column {first_child.start_point[1] + 1} "
                                f"(bytes {first_child.start_byte}-{first_child.end_byte})"
                            )

        self._traverse_tree_cursor(cursor, visit)
        return errors

    def parse(self, code: str, language: str) -> ParseResult:
        """Parse code using the specified language.

        Args:
            code: The code to parse.
            language: The language to use for parsing.

        Returns:
            A ParseResult object containing the parsed tree and metadata.

        Raises:
            ParseError: If the language is not supported or if parsing fails.
        """
        if not self.initialized:
            raise ParseError("Parser not initialized. Call initialize() first.")

        if language not in self._languages:
            raise ParseError(f"Language {language} not supported")

        parser = self._get_parser(language)
        tree = parser.parse(bytes(code, "utf8"))

        # Count lines and nodes
        line_count = len(code.splitlines())
        node_count = self._count_nodes(tree.root_node)

        # Find all errors in the tree
        errors = self._check_node_for_errors(tree.root_node)

        # Check if the tree is valid - any ERROR nodes or errors make it invalid
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
                # Set limits to prevent hanging
                query = self._queries[language]
                query.set_match_limit(100)  # Limit in-progress matches
                query.set_timeout_micros(1000000)  # 1 second timeout

                # Get matches using Tree-sitter's built-in matches() method
                matches = query.matches(tree.root_node)
                for match in matches:
                    for capture in match.captures:
                        if (
                            capture.name == "function_name"
                            and not capture.node.has_error
                        ):
                            name = capture.node.text.decode("utf8")
                            if name not in functions:
                                functions.append(name)
            except Exception as e:
                self._logger.warning(f"Query failed: {e}")

        # If query failed or no functions found, try cursor-based approach
        if not functions:
            functions = self._find_functions(tree)

        metadata = {
            "raw_content": code,
            "analysis": {"errors": errors, "warnings": [], "functions": functions},
            "root_type": tree.root_node.type,
            "encoding": "utf8",
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

    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """Parse a file using tree-sitter.

        Args:
            file_path: Path to the file to parse.

        Returns:
            ParseResult containing the parsed AST and metadata.

        Raises:
            ParseError: If file cannot be read or parsed.
        """
        file_path = Path(file_path)

        # Validate file exists
        if not file_path.exists():
            raise ParseError(f"File {file_path} not found")

        # Detect language from file extension
        language = self._get_language_for_file(file_path)
        if language is None:
            raise ParseError(f"Unsupported file extension: {file_path.suffix}")

        try:
            # Check if file is binary
            with open(file_path, "rb") as f:
                content_bytes = f.read(1024)
                if b"\x00" in content_bytes:
                    raise ParseError(f"File {file_path} is not a text file")

            # Read and parse file
            with open(file_path, "r", encoding=self._encoding) as f:
                content = f.read()

            result = self.parse(content, language)
            result.metadata["file_path"] = str(file_path)
            return result

        except UnicodeDecodeError:
            raise ParseError(f"File {file_path} is not a text file")
        except Exception as e:
            raise ParseError(f"Failed to parse file {file_path}: {e}")

    def cleanup(self) -> None:
        """Clean up parser resources."""
        self._parsers.clear()
        self._languages.clear()
        self._queries.clear()
        self._query_cache.clear()
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
