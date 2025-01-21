"""Tree-sitter parser implementation."""

from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Union
import logging
from pathlib import Path

from tree_sitter import (
    Language, 
    Parser, 
    Tree, 
    Node, 
    Query, 
    QueryError
)
from tree_sitter_language_pack import get_binding, get_language, get_parser

from src.GithubAnalyzer.core.models.errors import ParserError
from src.GithubAnalyzer.core.models.ast import NodeType
from src.GithubAnalyzer.core.services.base_service import BaseService
from src.GithubAnalyzer.core.services.file_service import FileService
from src.GithubAnalyzer.core.services.parsers.base import BaseParser
from src.GithubAnalyzer.common.services.cache_service import CacheService
from src.GithubAnalyzer.analysis.models.tree_sitter import (
    TreeSitterError,
    TreeSitterResult,
    TreeSitterQueryError
)

# Configure module logger
logger = logging.getLogger(__name__)

# Constants
QUERY_TIMEOUT_MS = 5000  # 5 seconds
MAX_RECOVERY_ATTEMPTS = 3
ERROR_SENTINEL = "ERROR"
MISSING_SENTINEL = "MISSING"
MAX_QUERY_MATCHES = 1000

def tree_sitter_logger(message: str) -> None:
    """Logger callback for Tree-sitter v24.
    
    Args:
        message: Log message from Tree-sitter
    """
    logger.debug("[tree-sitter] %s", message)


class TreeSitterParser(BaseParser):
    """Tree-sitter based code parser."""

    def __init__(self, cache_service=None, context_manager=None, file_service=None):
        """Initialize tree-sitter parser."""
        super().__init__()
        self.cache_service = cache_service
        self._context = context_manager
        self.file_service = file_service
        self.languages: Dict[str, Language] = {}
        self.parsers: Dict[str, Parser] = {}
        self._source_map: Dict[Tree, bytes] = {}
        self.language_names: Dict[Language, str] = {}
        
        # Configure Tree-sitter logging
        for parser_cls in [Parser, Language, Tree, Node]:
            if hasattr(parser_cls, 'set_logger'):
                parser_cls.set_logger(tree_sitter_logger)
        
        self.initialize()

    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize parser with supported languages."""
        try:
            logger.info("Initializing Tree-sitter parser")
            
            # Get languages from tree-sitter-language-pack
            for lang_id in languages or ["python", "javascript", "typescript"]:
                try:
                    # Get language and parser from language pack
                    lang = get_language(lang_id)
                    parser = get_parser(lang_id)
                    
                    # Store language and parser
                    self.languages[lang_id] = lang
                    self.parsers[lang_id] = parser
                    self.language_names[lang] = lang_id
                    
                    # Configure parser
                    parser.timeout_micros = QUERY_TIMEOUT_MS * 1000
                    
                    logger.info(f"Successfully initialized {lang_id} language support")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize {lang_id}: {e}")
                    continue
                    
            logger.info(f"Parser initialization complete with languages: {', '.join(self.languages.keys())}")
            
        except Exception as e:
            logger.error(f"Failed to initialize parser: {e}")
            raise

    def parse(self, content: Union[str, bytes], language: str, recovery_enabled: bool = True) -> TreeSitterResult:
        """Parse content using tree-sitter.
        
        Args:
            content: Source code to parse (string or bytes)
            language: Language identifier
            recovery_enabled: Whether to attempt error recovery
            
        Returns:
            TreeSitterResult containing parse results
            
        Raises:
            ParserError if language not supported or parsing fails
        """
        if language not in self.languages:
            logger.error("Unsupported language: %s", language)
            raise ValueError(f"Language {language} not supported")
            
        try:
            logger.debug("Starting parse of %d bytes with language %s", len(content), language)
            parser = self.parsers[language]
            
            # Parse content - handle both string and bytes input
            if isinstance(content, str):
                content = content.encode('utf8')
            
            # Keep reference to original tree
            tree = parser.parse(content)
            if tree is None:
                raise ValueError("Parser returned None - possible timeout")
            
            # Store source for this tree
            self._source_map[tree] = content
            
            # Get error nodes before any modifications
            error_nodes = self._get_error_nodes(tree.root_node)
            errors = [TreeSitterError.from_node(node, content.splitlines()) for node in error_nodes]
            
            # Create result with all required fields
            result = TreeSitterResult(
                tree=tree,  # Original tree reference
                language=language,
                is_valid=not tree.root_node.has_error,
                errors=errors,
                node_count=tree.root_node.descendant_count,
                metadata={
                    'content_hash': hash(content),
                    'recovery_enabled': recovery_enabled,
                    'parse_time_micros': parser.timeout_micros
                }
            )

            # Log parse results
            logger.info("Parse complete: valid=%s, nodes=%d, errors=%d, recovery_attempts=%d",
                       result.is_valid, result.node_count,
                       len(result.errors),
                       0 if result.is_valid else 1)

            return result
            
        except Exception as e:
            logger.error("Parsing failed for language %s: %s", language, str(e))
            raise

    def parse_file(self, file_path: Path, language: Optional[str] = None) -> TreeSitterResult:
        """Parse a file using tree-sitter.
        
        Args:
            file_path: Path to file
            language: Optional language override
            
        Returns:
            TreeSitterResult containing parse results
            
        Raises:
            ParserError if file cannot be read or parsed
        """
        try:
            logger.debug("Reading file: %s", file_path)
            # Read file directly if no file service
            if self.file_service:
                content = self.file_service.read_file(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # Detect language if not provided
            if not language:
                language = self._detect_language(file_path)
                if not language:
                    raise ParserError(f"Could not detect language for file: {file_path}")
                    
            return self.parse(content, language)
            
        except Exception as e:
            logger.error("Failed to parse %s: %s", file_path, e, exc_info=True)
            raise

    def _get_error_nodes(self, node: Node) -> List[Node]:
        """Find all error nodes in the AST.
        
        Args:
            node: Root node to start search from
            
        Returns:
            List of nodes with syntax errors
        """
        errors = []
        cursor = node.walk()
        
        reached_end = False
        while not reached_end:
            current_node = cursor.node
            
            if current_node.has_error or current_node.is_missing or current_node.type == ERROR_SENTINEL:
                logger.debug(
                    "Found error node: type=%s, line=%d, has_error=%s, is_missing=%s",
                    current_node.type,
                    current_node.start_point[0] + 1,
                    current_node.has_error,
                    current_node.is_missing
                )
                errors.append(current_node)
                
            if cursor.goto_first_child():
                continue
                
            if cursor.goto_next_sibling():
                continue
                
            retracing = True
            while retracing:
                if not cursor.goto_parent():
                    retracing = False
                    reached_end = True
                elif cursor.goto_next_sibling():
                    retracing = False
                    
        return errors

    def _attempt_recovery(self, node: Node, language: str) -> bool:
        """Attempt to recover from a parse error.
        
        Args:
            node: Error node to recover from
            language: Language being parsed
            
        Returns:
            True if recovery was successful
        """
        try:
            # Try basic recovery strategies
            if node.type == "ERROR":
                if language == "python":
                    # Check for missing colon
                    if self._is_missing_colon(node):
                        logger.debug("Attempting to recover from missing colon at line %d", 
                                   node.start_point[0] + 1)
                        
                        # Create and apply edit
                        edit = self.create_edit_for_missing_colon(node)
                        self.edit_tree(node.tree, [edit])
                        return True
                    
            return False
            
        except Exception as e:
            logger.error("Error during recovery attempt: %s", e)
            return False
        
    def _is_missing_colon(self, node: Node) -> bool:
        """Check if error is due to missing colon.
        
        Args:
            node: Error node to check
            
        Returns:
            True if error appears to be missing colon
        """
        try:
            # Get language object
            lang = self.languages["python"]
            
            # Create lookahead iterator for error node
            if not hasattr(node, 'parse_state'):
                return False
            
            lookahead = lang.lookahead_iterator(node.parse_state)
            valid_symbols = set(lookahead.iter_names())
            
            # Check if colon is a valid next symbol
            if ":" in valid_symbols:
                logger.debug("Found missing colon at line %d", node.start_point[0] + 1)
                return True
            
            # Check parent context
            parent = node.parent
            if parent and parent.type in {
                "function_definition",
                "class_definition",
                "if_statement",
                "for_statement",
                "while_statement",
                "try_statement"
            }:
                # These constructs require colons - check if we're at the point where colon is expected
                for child in parent.children:
                    if child == node and ":" in valid_symbols:
                        logger.debug("Found missing colon in %s at line %d", 
                                   parent.type, node.start_point[0] + 1)
                        return True
                    
            return False
            
        except Exception as e:
            logger.error("Error checking for missing colon: %s", e)
            return False

    def _create_query(self, language: str, query_string: str) -> Tuple[Query, List[TreeSitterQueryError]]:
        """Create a tree-sitter query with error handling.
        
        Args:
            language: Language to create query for
            query_string: Query pattern
            
        Returns:
            Tuple of (Query object, list of query errors)
            
        Raises:
            ParserError if query creation fails
        """
        try:
            logger.debug("Creating query for language %s", language)
            lang = self.languages[language]
            query = Query(lang, query_string)
            
            # Configure query limits
            query.disable_pattern(0)  # Prevent timeout on first match
            query.set_match_limit(MAX_QUERY_MATCHES)
            query.set_timeout_micros(QUERY_TIMEOUT_MS * 1000)  # Convert to microseconds
            
            logger.debug(
                "Query configured: patterns=%d, captures=%d, timeout=%dms",
                query.pattern_count, query.capture_count, QUERY_TIMEOUT_MS
            )
            
            errors = []
            
            # Check for predicate errors
            for pattern_index, pattern in enumerate(query.patterns):
                try:
                    if hasattr(pattern, 'validate_predicates'):
                        pattern.validate_predicates()
                except QueryError as e:
                    logger.warning(
                        "Invalid predicate in pattern %d: %s",
                        pattern_index, e
                    )
                    errors.append(TreeSitterQueryError.from_query(
                        query=query,
                        message=str(e),
                        pattern_index=pattern_index
                    ))
            
            if errors:
                logger.warning("Found %d query errors", len(errors))
            
            return query, errors
            
        except Exception as e:
            logger.error("Failed to create query: %s", e, exc_info=True)
            raise

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect language from file extension."""
        ext = file_path.suffix.lower()
        ext_map = {
            ".py": "python",
            ".js": "javascript", 
            ".ts": "typescript"
        }
        return ext_map.get(ext)

    def _get_default_languages(self) -> List[Tuple[str, str]]:
        """Get default supported languages.
        
        Returns:
            List of (language_id, library_path) tuples
        """
        # This would be configured based on installed language libraries
        return [
            ("python", "/usr/local/lib/tree-sitter-python.dylib"),
            ("javascript", "/usr/local/lib/tree-sitter-javascript.dylib"),
            ("typescript", "/usr/local/lib/tree-sitter-typescript.dylib")
        ]

    def _count_nodes(self, node: Node) -> int:
        """Count nodes in AST recursively.
        
        Args:
            node: Root node to count from
            
        Returns:
            Total number of nodes
        """
        count = 1  # Count current node
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def _validate_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate parser configuration."""
        return config or {}

    def cleanup(self) -> None:
        """Clean up parser resources."""
        self.languages.clear()
        self.parsers.clear()
        self._source_map.clear()
        logger.info("Tree-sitter parser cleaned up")

    def edit_tree(self, tree: Tree, edits: List[Dict[str, Any]]) -> Tree:
        """Apply edits to a tree-sitter tree.
        
        Args:
            tree: Tree to edit
            edits: List of edit operations
            
        Returns:
            New tree after edits
            
        Note:
            Tree-sitter requires edits to be applied in order and the tree kept in sync
        """
        try:
            # Get original source
            source = self._source_map.get(tree)
            if source is None:
                raise ValueError("No source found for tree")
            
            # Create edited source
            edited_source = bytearray(source)
            
            # Sort edits by position to ensure correct order
            sorted_edits = sorted(edits, key=lambda e: e['start_byte'])
            
            # Track offset adjustments
            offset = 0
            
            # Apply edits one at a time, keeping tree in sync
            for edit in sorted_edits:
                # Adjust positions for previous edits
                start_byte = edit['start_byte'] + offset
                old_end_byte = edit['old_end_byte'] + offset
                
                # Calculate new end byte based on text length
                text_len = len(edit['text'])
                new_end_byte = start_byte + text_len
                
                # Update source
                edited_source[start_byte:old_end_byte] = edit['text']
                
                # Keep tree in sync with edit
                tree.edit(
                    start_byte=start_byte,
                    old_end_byte=old_end_byte,
                    new_end_byte=new_end_byte,
                    start_point=edit['start_point'],
                    old_end_point=edit['old_end_point'],
                    new_end_point=edit['new_end_point']
                )
                
                # Update offset for next edit
                offset += text_len - (old_end_byte - start_byte)
            
            # Get parser for this tree's language
            parser = self.parsers[self.language_names[tree.language]]
            
            # Parse with edited source using old tree
            new_tree = parser.parse(bytes(edited_source), old_tree=tree)
            
            # Store source for new tree
            self._source_map[new_tree] = bytes(edited_source)
            
            return new_tree
            
        except Exception as e:
            logger.error("Failed to apply edits: %s", e)
            raise

    def create_edit_for_missing_colon(self, node: Node) -> Dict[str, Any]:
        """Create edit operation to add missing colon.
        
        Args:
            node: Node missing colon
            
        Returns:
            Edit operation dict
        """
        # Get position after node
        end_byte = node.end_byte
        end_point = node.end_point
        
        return {
            'start_byte': end_byte,
            'old_end_byte': end_byte,
            'new_end_byte': end_byte + 1,
            'start_point': end_point,
            'old_end_point': end_point,
            'new_end_point': (end_point[0], end_point[1] + 1),
            'text': b':'
        }

    def create_batch_edit(self, edits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create a batch of edits ensuring they don't conflict.
        
        Args:
            edits: List of edit operations
            
        Returns:
            Validated and sorted list of edits
        """
        # Sort edits by position to apply in correct order
        sorted_edits = sorted(edits, key=lambda e: (e['start_point'][0], e['start_point'][1]))
        
        # Validate edits don't overlap
        for i in range(len(sorted_edits) - 1):
            current = sorted_edits[i]
            next_edit = sorted_edits[i + 1]
            if current['new_end_point'] > next_edit['start_point']:
                raise ValueError(f"Overlapping edits at positions {current['new_end_point']} and {next_edit['start_point']}")
            
        return sorted_edits

    def create_edit_for_indent(self, node: Node, indent_level: int = 4) -> Dict[str, Any]:
        """Create edit to fix indentation.
        
        Args:
            node: Node to indent
            indent_level: Number of spaces per indent
            
        Returns:
            Edit operation dict
        """
        start_byte = node.start_byte
        start_point = node.start_point
        
        # Calculate required indentation
        current_indent = start_point[1]
        required_indent = indent_level * node.parent.children.index(node)
        indent_diff = required_indent - current_indent
        
        if indent_diff == 0:
            return None
        
        return {
            'start_byte': start_byte - current_indent,
            'old_end_byte': start_byte,
            'new_end_byte': start_byte - current_indent + required_indent,
            'start_point': (start_point[0], 0),
            'old_end_point': start_point,
            'new_end_point': (start_point[0], required_indent),
            'text': b' ' * required_indent
        }