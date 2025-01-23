"""Tree-sitter editor for handling incremental parsing and tree updates."""
from typing import Dict, List, Optional, Tuple, Union, Sequence
import logging
from dataclasses import dataclass
from pathlib import Path
from tree_sitter import Tree, Node, Point, Parser, Range

from src.GithubAnalyzer.core.models.errors import ParserError
from src.GithubAnalyzer.core.utils.logging import get_logger
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_traversal import TreeSitterTraversal
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_query import TreeSitterQueryHandler

logger = get_logger(__name__)

@dataclass
class EditOperation:
    """Represents a single edit operation on the tree."""
    start_byte: int
    old_end_byte: int
    new_end_byte: int
    start_point: Point
    old_end_point: Point
    new_end_point: Point
    old_text: str
    new_text: str

class TreeSitterLogHandler:
    """Handler for tree-sitter logging that integrates with our logging system."""
    def __init__(self):
        """Initialize the log handler."""
        self._enabled = False
        self.PARSE_TYPE = 0  # Tree-sitter parse event type
        self.LEX_TYPE = 1    # Tree-sitter lex event type
    
    def __call__(self, log_type: int, message: str) -> None:
        """Log a message from tree-sitter.
        
        Args:
            log_type: 0 for parse events, 1 for lex events
            message: The log message
        """
        if not self._enabled:
            return
            
        # Use INFO level to match logging config
        if log_type == self.PARSE_TYPE:
            logger.info(f"[PARSE] {message.strip()}", stacklevel=2)
        elif log_type == self.LEX_TYPE:
            logger.info(f"[LEX] {message.strip()}", stacklevel=2)
    
    def enable(self) -> None:
        """Enable logging."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable logging."""
        self._enabled = False

    def enable_parser_logging(self, parser: Parser) -> None:
        """Enable tree-sitter parser logging.
        
        Args:
            parser: The tree-sitter parser to enable logging for
        """
        self.enable()
        # Ensure the logger is properly set and bound
        parser.reset()  # Reset first to clear any existing logger
        parser.logger = self
        parser.reset()  # Reset again to ensure logger takes effect

    def disable_parser_logging(self, parser: Parser) -> None:
        """Disable tree-sitter parser logging.
        
        Args:
            parser: The tree-sitter parser to disable logging for
        """
        self.disable()
        parser.reset()  # Reset first to clear existing logger
        parser.logger = None
        parser.reset()  # Reset again to ensure logger is removed

class TreeSitterEditor:
    """Handles tree editing and incremental parsing."""

    def __init__(self):
        """Initialize editor with traversal and query utilities."""
        self._traversal = TreeSitterTraversal()
        self._query_handler = TreeSitterQueryHandler()
        self._tree_cache: Dict[str, Tuple[Tree, bytes]] = {}  # Store both tree and its source
        self._tree_backups: Dict[str, bytes] = {}  # Store source bytes separately
        self._log_handler = TreeSitterLogHandler()
        self._source_bytes: Dict[str, bytes] = {}  # Store source bytes separately

    def enable_parser_logging(self, parser: Parser) -> None:
        """Enable tree-sitter parser logging."""
        self._log_handler.enable_parser_logging(parser)

    def disable_parser_logging(self, parser: Parser) -> None:
        """Disable tree-sitter parser logging."""
        self._log_handler.disable_parser_logging(parser)

    def get_cached_tree(self, file_path: str) -> Optional[Tree]:
        """Get cached tree for a file."""
        cached = self._tree_cache.get(file_path)
        return cached[0] if cached else None

    def get_source_bytes(self, file_path: str) -> Optional[bytes]:
        """Get source bytes for a file."""
        cached = self._tree_cache.get(file_path)
        return cached[1] if cached else None

    def cache_tree(self, file_path: str, tree: Tree, source_bytes: Optional[bytes] = None) -> None:
        """Cache a tree and its source for a file.
        
        Args:
            file_path: Path to the file
            tree: Tree to cache
            source_bytes: Optional source bytes to store with tree
        """
        try:
            if not tree or not tree.root_node:
                logger.error("Cannot cache invalid tree")
                return

            # Get source bytes from input or try to get from tree
            if source_bytes is None:
                try:
                    source_bytes = tree.root_node.text
                except Exception as e:
                    logger.error(f"Failed to get source bytes from tree: {e}")
                    return

            # Store a copy of the source bytes and the original tree
            # We don't need to reparse here since the tree is already valid
            self._tree_cache[file_path] = (tree, bytes(source_bytes))
            
        except Exception as e:
            logger.error(f"Failed to cache tree: {str(e)}")

    def backup_tree(self, file_path: str) -> None:
        """Create a backup of the current tree state.
        
        Args:
            file_path: Path to the file to backup
        """
        try:
            cached = self._tree_cache.get(file_path)
            if not cached:
                logger.error("No tree in cache to backup")
                return
                
            tree, source_bytes = cached
            if not tree or not tree.root_node:
                logger.error("Cannot backup invalid tree")
                return

            # Store a copy of the source bytes only
            # We'll reparse during restore using the provided parser
            self._tree_backups[file_path] = bytes(source_bytes)
            
        except Exception as e:
            logger.error(f"Failed to backup tree: {str(e)}")

    def restore_tree(self, file_path: str, parser: Parser) -> bool:
        """Restore tree from backup.
        
        Args:
            file_path: Path to the file to restore
            parser: Parser to use for reparsing
            
        Returns:
            bool: True if restore succeeded, False otherwise
        """
        try:
            backup_bytes = self._tree_backups.get(file_path)
            if not backup_bytes:
                logger.error("Failed to restore tree from backup: No backup found")
                return False

            # Create a new copy of source bytes for restoration
            restore_bytes = bytes(backup_bytes)
            
            # Parse from scratch with the provided parser
            parser.reset()
            restored_tree = parser.parse(restore_bytes)
            
            if not restored_tree or not restored_tree.root_node:
                logger.error("Failed to restore tree from backup: Could not parse")
                return False
                
            if not self.verify_tree_changes(restored_tree):
                logger.error("Failed to restore tree from backup: Syntax errors in restored tree")
                return False
                
            # Cache the restored tree with its source
            self.cache_tree(file_path, restored_tree, restore_bytes)
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore tree from backup: {str(e)}")
            return False

    def get_changed_ranges(self, old_tree: Tree, new_tree: Tree) -> Sequence[Range]:
        """Get ranges that changed between two trees.
        
        According to v24 docs, this should be called right after parsing
        with the old tree that was passed to parse() and the new tree
        that was returned from it.
        
        Args:
            old_tree: The original tree before edits
            new_tree: The new tree after edits
            
        Returns:
            Sequence of Range objects indicating changed areas
        """
        try:
            return old_tree.changed_ranges(new_tree)
        except Exception as e:
            logger.error(f"Failed to get changed ranges: {e}")
            return []

    def visualize_tree(self, tree: Tree, output_path: Union[str, Path]) -> bool:
        """Write a DOT graph visualization of the tree.
        
        Args:
            tree: Tree to visualize
            output_path: Path to write DOT file
            
        Returns:
            True if visualization was successful
        """
        try:
            with open(output_path, 'w') as f:
                tree.print_dot_graph(f)
            return True
        except Exception as e:
            logger.error(f"Failed to write DOT graph: {e}")
            return False

    def get_tree_with_offset(
        self,
        tree: Tree,
        offset_bytes: int,
        offset_extent: Tuple[int, int]
    ) -> Optional[Node]:
        """Get tree root node with offset.
        
        Args:
            tree: Source tree
            offset_bytes: Byte offset to apply
            offset_extent: Tuple of (row, column) offset
            
        Returns:
            Root node with applied offset
        """
        try:
            return tree.root_node_with_offset(offset_bytes, offset_extent)
        except Exception as e:
            logger.error(f"Failed to get tree with offset: {e}")
            return None

    def is_valid_position(self, tree: Tree, position: Point) -> bool:
        """Check if a position is valid within the tree."""
        if not tree or not tree.root_node:
            return False
            
        # Get tree bounds
        start_row, start_col = tree.root_node.start_point
        end_row, end_col = tree.root_node.end_point
        pos_row, pos_col = position
        
        # Check if position is within bounds
        if pos_row < start_row or pos_row > end_row:
            return False
            
        # For same line positions, check column bounds
        if pos_row == start_row and pos_col < start_col:
            return False
        if pos_row == end_row and pos_col > end_col:
            return False
            
        return True

    def create_edit_operation(
        self,
        tree: Tree,
        old_text: str,
        new_text: str,
        start_position: Point
    ) -> EditOperation:
        """Create an edit operation from text changes.
        
        Args:
            tree: Tree to edit
            old_text: Text to replace
            new_text: New text
            start_position: Starting position of edit
            
        Returns:
            EditOperation: Edit operation to apply
            
        Raises:
            ParserError: If edit position is invalid or text doesn't match
        """
        # Find node at edit position using traversal
        node = self._traversal.find_node_at_point(tree.root_node, start_position)
        if not node:
            raise ParserError(f"Invalid edit position: {start_position}")
            
        # Get source bytes and verify position
        source_bytes = tree.root_node.text
        lines = source_bytes.split(b'\n')
        
        # Calculate start_byte by counting bytes up to the position
        start_byte = 0
        for i in range(start_position[0]):
            start_byte += len(lines[i]) + 1  # +1 for newline
        start_byte += len(lines[start_position[0]][:start_position[1]].decode('utf8').encode('utf8'))
        
        # Get actual old text from source to verify
        old_text_bytes = old_text.encode('utf8')
        actual_old_text = source_bytes[start_byte:start_byte + len(old_text_bytes)].decode('utf8')
        if actual_old_text != old_text:
            raise ParserError(f"Text mismatch at position {start_position}: expected '{old_text}', found '{actual_old_text}'")
            
        # Calculate end bytes
        old_end_byte = start_byte + len(old_text_bytes)
        new_end_byte = start_byte + len(new_text.encode('utf8'))
        
        # Calculate end points
        old_lines = old_text.split('\n')
        new_lines = new_text.split('\n')
        
        # For old text end point
        if len(old_lines) == 1:
            old_end_point = Point(
                row=start_position[0],
                column=start_position[1] + len(old_text)
            )
        else:
            old_end_point = Point(
                row=start_position[0] + len(old_lines) - 1,
                column=len(old_lines[-1])
            )
            
        # For new text end point    
        if len(new_lines) == 1:
            new_end_point = Point(
                row=start_position[0],
                column=start_position[1] + len(new_text)
            )
        else:
            new_end_point = Point(
                row=start_position[0] + len(new_lines) - 1,
                column=len(new_lines[-1])
            )

        return EditOperation(
            start_byte=start_byte,
            old_end_byte=old_end_byte,
            new_end_byte=new_end_byte,
            start_point=start_position,
            old_end_point=old_end_point,
            new_end_point=new_end_point,
            old_text=old_text,
            new_text=new_text
        )

    def apply_edit(self, tree: Tree, edit: EditOperation) -> None:
        """Apply an edit operation to a tree.
        
        Args:
            tree: Tree to edit
            edit: Edit operation to apply
            
        Raises:
            ParserError: If edit application fails
        """
        try:
            # Verify tree is valid
            if not tree or not tree.root_node:
                raise ParserError("Cannot apply edit to invalid tree")
                
            # Verify edit position is valid
            node = self._traversal.find_node_at_point(tree.root_node, edit.start_point)
            if not node:
                raise ParserError(f"Invalid edit position: {edit.start_point}")
                
            # Get source bytes and verify old text
            source_bytes = tree.root_node.text
            actual_old_text = source_bytes[edit.start_byte:edit.old_end_byte].decode('utf8')
            if actual_old_text != edit.old_text:
                raise ParserError(f"Text mismatch: expected '{edit.old_text}', found '{actual_old_text}'")
                
            # Apply edit to tree
            tree.edit(
                start_byte=edit.start_byte,
                old_end_byte=edit.old_end_byte,
                new_end_byte=edit.new_end_byte,
                start_point=edit.start_point,
                old_end_point=edit.old_end_point,
                new_end_point=edit.new_end_point
            )
            
        except Exception as e:
            logger.error(f"Failed to apply edit: {e}")
            raise ParserError(f"Failed to apply edit: {e}")

    def verify_tree_changes(self, tree: Tree) -> bool:
        """Verify that a tree has no syntax errors.
        
        Args:
            tree: Tree to verify
            
        Returns:
            bool: True if tree is valid, False if it has errors
        """
        if not tree or not tree.root_node:
            logger.error("Cannot verify invalid tree")
            return False
            
        # Check if tree has errors using root node property
        if tree.root_node.has_error:
            logger.error("Tree contains syntax errors")
            return False
            
        # Use cursor-based traversal for efficiency
        cursor = tree.root_node.walk()
        reached_root = False
        
        while not reached_root:
            node = cursor.node
            
            # Check for error nodes
            if node.type == "ERROR" or node.is_missing:
                logger.error(f"Found error node: {node.type} at {node.start_point}")
                return False
                
            # Try to move to first child
            if cursor.goto_first_child():
                continue
                
            # Try to move to next sibling
            if cursor.goto_next_sibling():
                continue
                
            # Move up until we find a parent with next sibling
            while not reached_root:
                if not cursor.goto_parent():
                    reached_root = True
                    break
                    
                if cursor.goto_next_sibling():
                    break
                    
        return True

    def update_tree(
        self,
        file_path: str,
        edits: List[EditOperation],
        parser: Parser
    ) -> Optional[Tree]:
        """Update a tree with edits.
        
        Args:
            file_path: Path to file being edited
            edits: List of edit operations to apply
            parser: Parser instance to use
            
        Returns:
            Tree: Updated tree if successful, None if failed
        """
        # Get cached tree and source
        tree = self.get_cached_tree(file_path)
        if not tree:
            return None
            
        # Create working copies
        working_tree = tree.copy()
        source_bytes = working_tree.root_node.text
        
        # Sort edits by start_byte in reverse order
        sorted_edits = sorted(edits, key=lambda e: e.start_byte, reverse=True)
        
        # Apply edits to source
        updated_source = source_bytes
        for edit in sorted_edits:
            # Verify edit position
            node = self._traversal.find_node_at_point(working_tree.root_node, edit.start_point)
            if not node:
                logger.error(f"Invalid edit position: {edit.start_point}")
                return None
                
            # Get actual old text from current source
            actual_old_text = updated_source[edit.start_byte:edit.old_end_byte].decode('utf8')
            if actual_old_text != edit.old_text:
                logger.error(
                    f"Text mismatch at position {edit.start_point}: "
                    f"expected '{edit.old_text}', found '{actual_old_text}'"
                )
                return None
                
            # Apply edit to source
            updated_source = (
                updated_source[:edit.start_byte] +
                edit.new_text.encode('utf8') +
                updated_source[edit.old_end_byte:]
            )
            
            # Apply edit to working tree
            try:
                working_tree.edit(
                    start_byte=edit.start_byte,
                    old_end_byte=edit.old_end_byte,
                    new_end_byte=edit.new_end_byte,
                    start_point=edit.start_point,
                    old_end_point=edit.old_end_point,
                    new_end_point=edit.new_end_point
                )
            except Exception as e:
                logger.error(f"Failed to apply edit: {e}")
                return None
                
        # Parse updated source
        parser.reset()
        new_tree = parser.parse(updated_source, working_tree)
        if not new_tree:
            logger.error("Failed to parse updated source")
            return None
            
        # Verify tree is valid
        if new_tree.root_node.has_error:
            logger.warning("Updated tree contains syntax errors")
            return None
            
        # Cache and return new tree
        self.cache_tree(file_path, new_tree, updated_source)
        return new_tree

    def reparse_tree(self, tree: Tree, new_source: str, parser: Parser) -> Tree:
        """Reparse a tree with new source code.
        
        Args:
            tree: Original tree to reparse
            new_source: New source code
            parser: Parser to use
            
        Returns:
            Tree: New parsed tree
            
        Raises:
            ParserError: If parsing fails or produces an invalid tree
        """
        try:
            # Verify input tree
            if not tree or not tree.root_node:
                raise ParserError("Cannot reparse invalid tree")
                
            # Convert source to bytes
            source_bytes = bytes(new_source, 'utf8')
            
            # Reset parser and parse with old tree
            parser.reset()
            new_tree = parser.parse(source_bytes, tree)
            
            if not new_tree or not new_tree.root_node:
                raise ParserError("Failed to parse tree: Invalid parse result")
                
            # Verify new tree has no syntax errors
            if new_tree.root_node.has_error:
                raise ParserError("Syntax error in reparsed tree")
                
            # Walk tree to find any ERROR nodes
            for node in self._traversal.walk_tree(new_tree.root_node):
                if node.type == "ERROR" or node.is_missing:
                    raise ParserError(f"Found error node: {node.type} at {node.start_point}")
                    
            return new_tree
            
        except Exception as e:
            raise ParserError(f"Failed to reparse tree: {str(e)}") 