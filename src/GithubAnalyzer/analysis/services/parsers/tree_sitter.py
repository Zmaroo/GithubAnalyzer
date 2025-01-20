"""Tree-sitter based parser implementation."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Set, Callable
from threading import Lock

from tree_sitter import Language, Parser, Tree, Node
from tree_sitter_language_pack import get_binding, get_language, get_parser

from ....core.models.errors import ParserError
from ....core.models.file import FileInfo, FileType
from ...models.tree_sitter import (
    TreeSitterConfig,
    TreeSitterError,
    TreeSitterResult,
    TreeSitterNodeType,
    TreeSitterLogType,
    TreeSitterRange,
    TreeSitterEdit,
    TreeSitterLanguageBinding
)
from ....core.services.file_service import FileService
from ....core.services.parsers.base import BaseParser
from ....common.services.cache_service import CacheService
from ....core.utils.context_manager import ContextManager
from ....core.utils.decorators import retry, timeout, timer
from ....core.utils.logging import get_logger
from ....core.services.base_service import BaseService

logger = get_logger(__name__)


class TreeSitterParser(BaseService):
    """Parser implementation using tree-sitter."""

    def __init__(
        self,
        config: Optional[TreeSitterConfig] = None,
        file_service: Optional[FileService] = None,
        cache_service: Optional[CacheService] = None,
        context_manager: Optional[ContextManager] = None
    ) -> None:
        """Initialize the parser.
        
        Args:
            config: Parser configuration
            file_service: Service for file operations
            cache_service: Service for caching results
            context_manager: Service for resource management
        """
        super().__init__()
        self._config = config or TreeSitterConfig(languages=self._get_default_languages())
        self._file_service = file_service or FileService()
        self._cache = cache_service or CacheService()
        self._context = context_manager or ContextManager()
        
        self._lock = Lock()
        self._initialized = False
        self._language_bindings: Dict[str, TreeSitterLanguageBinding] = {}
        self._changed_files: Set[Path] = set()
        
        # Set up logging callback for tree-sitter v24
        self._setup_logging()

    @property
    def initialized(self) -> bool:
        """Whether the parser is initialized."""
        return self._initialized

    @property
    def supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self._language_bindings.keys())

    def _setup_logging(self) -> None:
        """Set up logging callback for tree-sitter v24."""
        def log_callback(message: str) -> None:
            """Callback for tree-sitter logging.
            
            Args:
                message: The log message
            """
            if not self._config.debug:
                return
                
            logger.debug("[tree-sitter] debug: %s", message)
            
        # Store callback to prevent garbage collection
        self._log_callback = log_callback
        
    def set_debug(self, enabled: bool) -> None:
        """Enable or disable debug logging.
        
        Args:
            enabled: Whether to enable debug logging
        """
        self._config.debug = enabled
        
    def initialize(self, languages: Optional[List[str]] = None) -> None:
        """Initialize the parser with specified languages.
        
        Args:
            languages: List of languages to initialize. If None, uses configured languages.
            
        Raises:
            ParserError: If initialization fails
        """
        try:
            logger.info("Initializing parser with languages: %s", languages or self._config.languages)
            
            # Use provided languages or fall back to configured ones
            languages_to_init = languages or self._config.languages
            
            # Track which languages were initialized
            initialized_languages = []
            
            for language in languages_to_init:
                try:
                    # Get language binding and parser
                    binding = get_binding(language)
                    language_obj = get_language(language)
                    parser = get_parser(language)
                    
                    # Store language binding
                    self._language_bindings[language] = TreeSitterLanguageBinding(
                        name=language,
                        binding=binding,
                        language=language_obj,
                        parser=parser
                    )
                    
                    initialized_languages.append(language)
                    logger.debug("[tree-sitter] Initialized language: %s", language)
                    
                except Exception as e:
                    logger.warning("Failed to initialize language %s: %s", language, e)
                    continue
            
            # Set initialized if at least one language was initialized
            if initialized_languages:
                self._initialized = True
            else:
                raise ParserError("No languages were initialized successfully")

        except Exception as e:
            if not isinstance(e, ParserError):
                raise ParserError(f"Failed to initialize parser: {str(e)}")
            raise

    @retry(max_attempts=2)
    @timer(name="parse")
    def parse(self, content: Union[str, bytes], language: str) -> TreeSitterResult:
        """Parse content using tree-sitter.
        
        Args:
            content: Content to parse
            language: Language to use for parsing
            
        Returns:
            TreeSitterResult containing AST and metadata
            
        Raises:
            ParserError: If parsing fails
        """
        try:
            if not self._initialized:
                raise ParserError("Parser not initialized")
                
            if language not in self._language_bindings:
                raise ParserError(f"Language {language} not supported")
                
            # Get parser for language
            binding = self._language_bindings[language]
            parser = binding.parser
            
            # Convert content to bytes if needed
            if isinstance(content, str):
                content = content.encode()
                
            # Log parsing attempt
            logger.info(f"Parsing {language} content ({len(content)} bytes)")
            
            # Parse content
            if self._config.debug:
                logger.debug("[tree-sitter] debug: Starting parse")
                
            tree = parser.parse(content)
            
            if self._config.debug:
                logger.debug("[tree-sitter] debug: Parse complete")
            
            # Check for syntax errors
            errors = []
            for node in self._get_error_nodes(tree.root_node):
                error = TreeSitterError(
                    message=f"Syntax error at {node.type}",
                    range=TreeSitterRange.from_tree_sitter(node.range),
                    node=node
                )
                errors.append(error)
                logger.warning(f"Syntax error in {language} content: {error.message} at line {error.line}, column {error.column}")
            
            # Create result
            result = TreeSitterResult(
                tree=tree,
                language=language,
                errors=errors,
                is_valid=len(errors) == 0,
                node_count=self._count_nodes(tree.root_node),
                metadata={
                    "root_type": tree.root_node.type,
                    "byte_length": len(content),
                    "line_count": content.count(b"\n") + 1
                }
            )
            
            # Print tree if configured
            if self._config.print_tree:
                result.print_tree()
                
            # Log success
            logger.info(f"Successfully parsed {language} content: {result.node_count} nodes, {len(errors)} errors")
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse {language} content: {str(e)}", exc_info=True)
            raise ParserError(f"Failed to parse content: {e}")

    @retry(max_attempts=2)
    @timer(name="parse_file")
    def parse_file(self, file_path: Union[str, Path, FileInfo]) -> TreeSitterResult:
        """Parse a file using tree-sitter.
    
        Args:
            file_path: Path to the file to parse or FileInfo object
    
        Returns:
            TreeSitterResult containing AST and metadata
    
        Raises:
            ParserError: If parsing fails
        """
        try:
            # Get file info
            if isinstance(file_path, FileInfo):
                file_info = file_path
                path = file_info.path
            else:
                path = Path(file_path)
                file_info = self._file_service.get_file_info(path)

            # Check cache first
            cache_key = str(path.resolve())
            if cache_key not in self._changed_files:
                cached_ast = self._cache.get("ast", cache_key)
                if cached_ast:
                    return cached_ast

            # Validate file
            if file_info.is_binary:
                raise ParserError(f"Cannot parse binary file: {path}")

            if file_info.file_type == FileType.UNKNOWN:
                raise ParserError(f"Unsupported file type: {path}")

            # Read and parse file
            content = path.read_text(encoding=file_info.encoding)
            result = self.parse(content, file_info.file_type.value)

            # Cache the result
            self._cache.set("ast", cache_key, result)
            self._changed_files.discard(cache_key)

            return result

        except Exception as e:
            raise ParserError(f"Failed to parse file: {str(e)}")

    def edit_file(self, file_path: Union[str, Path], edit: TreeSitterEdit) -> None:
        """Apply an edit to a previously parsed file.
        
        Args:
            file_path: Path to the file
            edit: Edit operation to apply
            
        Raises:
            ParserError: If edit fails
        """
        try:
            file_path = Path(file_path)
            cache_key = str(file_path.resolve())
            
            # Get cached tree
            cached_result = self._cache.get("ast", cache_key)
            if not cached_result:
                raise ParserError(f"No cached AST found for {file_path}")
                
            # Apply edit to tree
            cached_result.tree.edit(
                start_byte=edit.start_byte,
                old_end_byte=edit.old_end_byte,
                new_end_byte=edit.new_end_byte,
                start_point=edit.start_point,
                old_end_point=edit.old_end_point,
                new_end_point=edit.new_end_point
            )
            
            # Mark file as changed
            self._changed_files.add(cache_key)
            
        except Exception as e:
            raise ParserError(f"Failed to apply edit: {e}")

    def get_changed_ranges(
        self, 
        file_path: Union[str, Path],
        new_content: Union[str, bytes]
    ) -> List[TreeSitterRange]:
        """Get ranges that changed between cached and new content.
        
        Args:
            file_path: Path to the file
            new_content: New content to compare against
            
        Returns:
            List of changed ranges
            
        Raises:
            ParserError: If comparison fails
        """
        try:
            file_path = Path(file_path)
            cache_key = str(file_path.resolve())
            
            # Get cached tree
            cached_result = self._cache.get("ast", cache_key)
            if not cached_result:
                raise ParserError(f"No cached AST found for {file_path}")
                
            # Parse new content
            if isinstance(new_content, str):
                new_content = new_content.encode()
                
            new_tree = cached_result.tree.copy()
            new_tree = self._language_bindings[cached_result.language].parser.parse(new_content)
            
            # Get changed ranges
            ranges = cached_result.tree.changed_ranges(new_tree)
            return [TreeSitterRange.from_tree_sitter(r) for r in ranges]
            
        except Exception as e:
            raise ParserError(f"Failed to get changed ranges: {e}")

    def cleanup(self) -> None:
        """Clean up parser resources."""
        with self._lock:
            self._context.stop()
            self._cache.cleanup()
            self._language_bindings.clear()
            self._changed_files.clear()
            self._initialized = False

    def _get_error_nodes(self, node: Node) -> List[Node]:
        """Get all error nodes in the tree using efficient cursor traversal.
        
        Args:
            node: Root node to start traversal from
            
        Returns:
            List of nodes containing syntax errors
        """
        errors = []
        cursor = node.walk()
        
        # Visit all nodes in the tree efficiently
        while True:
            if cursor.node.has_error:
                errors.append(cursor.node)
                
            # Try to move to first child
            if cursor.goto_first_child():
                continue
                
            # No children, try to move to next sibling
            if cursor.goto_next_sibling():
                continue
                
            # No siblings, move up and try next sibling
            retracing = True
            while retracing:
                if not cursor.goto_parent():
                    # Reached the root, traversal complete
                    return errors
                    
                if cursor.goto_next_sibling():
                    retracing = False
                    
        return errors

    def _get_default_languages(self) -> List[str]:
        """Get list of default supported languages."""
        return ["python", "javascript", "typescript"]

    def _count_nodes(self, node: Node) -> int:
        """Count nodes in AST recursively."""
        count = 1  # Count current node
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            The validated configuration dictionary
            
        Raises:
            ConfigError: If configuration is invalid
        """
        # No config needed for tree-sitter parser
        return config
