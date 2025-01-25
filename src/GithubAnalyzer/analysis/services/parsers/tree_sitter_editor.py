"""Tree-sitter editor for handling incremental parsing and tree updates."""
from typing import Dict, List, Optional, Tuple, Union, Sequence
from dataclasses import dataclass
from pathlib import Path
from tree_sitter import Tree, Node, Point, Parser, Range, Query
import logging
import sys

from src.GithubAnalyzer.core.models.errors import ParserError
from src.GithubAnalyzer.core.utils.logging import get_logger
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_traversal import TreeSitterTraversal
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_query import TreeSitterQueryHandler
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_logging import TreeSitterLogHandler
from tree_sitter_language_pack import get_language

logger = get_logger(__name__)

@dataclass
class EditOperation:
    """Represents a single edit operation on the tree."""
    old_text: str
    new_text: str
    start_position: Point
    end_position: Optional[Point] = None

class TreeSitterEditor:
    """Handles tree editing and incremental parsing."""

    def __init__(self):
        """Initialize editor with traversal and query utilities."""
        self._traversal = TreeSitterTraversal()
        self._log_handler = TreeSitterLogHandler()
        self._query_handler = TreeSitterQueryHandler(self._log_handler)
        self._log_handler.enable()  # Enable logging by default

    def enable_parser_logging(self, parser: Parser) -> None:
        """Enable tree-sitter parser logging.
        
        Args:
            parser: Parser to enable logging for
        """
        self._log_handler.enable_parser_logging(parser)
        # Enable DOT graph debugging in debug mode
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            try:
                parser.print_dot_graphs(sys.stderr)
            except AttributeError:
                self._log_handler.warning("DOT graph debugging not supported in this version")

    def disable_parser_logging(self, parser: Parser) -> None:
        """Disable logging for a parser."""
        try:
            if hasattr(parser, "logger"):
                parser.logger = None
        except AttributeError:
            pass
        
        try:
            parser.print_dot_graphs(None)
        except AttributeError:
            self._log_handler.warning("DOT graph debugging not supported in this version")

    def get_changed_ranges(self, old_tree: Tree, new_tree: Tree) -> List[Range]:
        """Get ranges that changed between trees."""
        return old_tree.changed_ranges(new_tree)

    def visualize_tree(self, tree: Tree, output_path: str) -> bool:
        """Visualize a tree and save to file."""
        try:
            with open(output_path, 'w') as f:
                f.write(str(tree.root_node))  # Use str() instead of sexp()
            return True
        except Exception as e:
            self._log_handler.error(f"Failed to visualize tree: {str(e)}")
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

    def verify_tree_changes(self, tree: Tree) -> bool:
        """Verify if a tree has valid changes."""
        if not tree or not tree.root_node:
            return False
            
        return self._query_handler.is_valid_node(tree.root_node)

    def create_edit_operation(
        self,
        tree: Tree,
        old_text: str,
        new_text: str,
        start_position: Point,
        end_position: Optional[Point] = None
    ) -> EditOperation:
        """Create an edit operation."""
        if not self._validate_tree(tree, "create_edit"):
            raise ParserError("Cannot create edit for invalid tree")
            
        if not self.is_valid_position(tree, start_position):
            raise ParserError(f"Invalid start position: {start_position}")
            
        if end_position and not self.is_valid_position(tree, end_position):
            raise ParserError(f"Invalid end position: {end_position}")
            
        return EditOperation(
            old_text=old_text,
            new_text=new_text,
            start_position=start_position,
            end_position=end_position
        )

    def apply_edit(self, tree: Tree, edit: EditOperation) -> None:
        """Apply an edit operation to a tree."""
        if not self._validate_tree(tree, "apply_edit"):
            raise ParserError("Cannot apply edit to invalid tree")

        try:
            self._log_handler.info(f"Applying edit: {edit.old_text} -> {edit.new_text} at {edit.start_position}")
            start_byte = self._get_byte_offset(tree, edit.start_position)
            end_byte = (self._get_byte_offset(tree, edit.end_position) 
                       if edit.end_position 
                       else start_byte + len(edit.old_text.encode('utf8')))
            
            self._log_handler.debug(f"Edit byte range: {start_byte} -> {end_byte}")
                       
            tree.edit(
                start_byte=start_byte,
                old_end_byte=end_byte,
                new_end_byte=start_byte + len(edit.new_text.encode('utf8')),
                start_point=edit.start_position,
                old_end_point=edit.end_position or edit.start_position,
                new_end_point=self._calculate_new_end_point(
                    edit.start_position,
                    edit.new_text
                )
            )
            self._log_handler.info("Edit applied successfully")
        except Exception as e:
            self._log_handler.error(f"Failed to apply edit: {e}", exc_info=True)
            raise ParserError(f"Failed to apply edit: {str(e)}")

    def _validate_tree(self, tree: Tree, context: str = "") -> bool:
        """Validate a tree."""
        if not tree:
            self._log_handler.error(f"{context}: Tree is None")
            return False
        if not tree.root_node:
            self._log_handler.error(f"{context}: Tree has no root node")
            return False
        if tree.root_node.has_error:
            self._log_handler.warning(f"{context}: Tree contains errors")
        return True

    def update_tree(self, tree: Tree, edits: List[EditOperation], parser: Parser) -> Optional[Tree]:
        """Update a tree with edits using incremental parsing."""
        if not self._validate_tree(tree, "update"):
            self._log_handler.error("Cannot update invalid tree")
            return None

        try:
            # Apply edits
            self._log_handler.info(f"Applying {len(edits)} edits to tree")
            
            # Build new source by applying edits
            source_bytes = bytearray(tree.root_node.text)  # Get initial source from root node
            self._log_handler.debug(f"Initial source length: {len(source_bytes)} bytes")
            
            # Apply edits in reverse order to maintain byte offsets
            for edit in reversed(edits):
                self._log_handler.info(f"Applying edit: {edit.old_text} -> {edit.new_text} at {edit.start_position}")
                start_byte = self._get_byte_offset(tree, edit.start_position)
                end_byte = (self._get_byte_offset(tree, edit.end_position) 
                          if edit.end_position 
                          else start_byte + len(edit.old_text.encode('utf8')))
                
                # Replace bytes in source
                new_bytes = edit.new_text.encode('utf8')
                source_bytes[start_byte:end_byte] = new_bytes
                self._log_handler.debug(f"Updated source length: {len(source_bytes)} bytes")
                
                # Apply edit to tree for tracking
                tree.edit(
                    start_byte=start_byte,
                    old_end_byte=end_byte,
                    new_end_byte=start_byte + len(new_bytes),
                    start_point=edit.start_position,
                    old_end_point=edit.end_position or edit.start_position,
                    new_end_point=self._calculate_new_end_point(
                        edit.start_position,
                        edit.new_text
                    )
                )
                self._log_handler.info("Edit applied successfully")

            # Reparse with timeout
            self._log_handler.debug("Reparsing tree with timeout")
            parser.reset()  # Reset parser state
            parser.timeout_micros = 100000  # 100ms timeout
            new_tree = parser.parse(bytes(source_bytes), tree)

            if not new_tree or not new_tree.root_node:
                self._log_handler.error("Parser produced invalid tree")
                raise ParserError("Parser failed to produce valid tree")

            self._log_handler.info("Tree updated successfully")
            return new_tree

        except Exception as e:
            self._log_handler.error(f"Failed to update tree: {str(e)}", exc_info=True)
            return None

    def reparse_tree(self, tree: Tree, new_source: str, parser: Parser) -> Tree:
        """Reparse a tree with new source code using incremental parsing."""
        if not self._validate_tree(tree, "reparse"):
            raise ParserError("Cannot reparse invalid tree")
            
        try:
            # Convert source to bytes and parse incrementally
            source_bytes = new_source.encode('utf8')
            parser.reset()
            
            # Parse with old tree for incremental parsing
            new_tree = parser.parse(source_bytes, tree)
            
            if not new_tree or not new_tree.root_node:
                raise ParserError("Parser failed to produce valid tree")
                
            return new_tree

        except Exception as e:
            self._log_handler.error(f"Failed to parse tree: {e}", exc_info=True)
            raise ParserError(f"Failed to parse tree: {str(e)}")

    def _get_byte_offset(self, tree: Tree, position: Point) -> int:
        """Get byte offset for a position."""
        if not tree or not tree.root_node:
            raise ParserError("Cannot get byte offset: Invalid tree")
            
        try:
            return position[1]  # Column is byte offset in line
        except Exception as e:
            raise ParserError(f"Failed to get byte offset: {str(e)}")

    def _calculate_new_end_point(self, start: Point, text: str) -> Point:
        """Calculate end point after inserting text."""
        lines = text.split('\n')
        if len(lines) == 1:
            return Point(start[0], start[1] + len(text.encode('utf8')))
        else:
            return Point(
                start[0] + len(lines) - 1,
                len(lines[-1].encode('utf8'))
            )

    def _verify_edit_position(self, node: Node, position: Point, text: str) -> bool:
        """Verify if an edit position is valid."""
        if not node:
            return False
        
        # Check if position is within node bounds
        if position[0] < node.start_point[0] or position[0] > node.end_point[0]:
            return False
        
        # For same line edits, check column bounds
        if position[0] == node.start_point[0] and position[1] < node.start_point[1]:
            return False
        if position[0] == node.end_point[0] and position[1] > node.end_point[1]:
            return False
        
        return True 