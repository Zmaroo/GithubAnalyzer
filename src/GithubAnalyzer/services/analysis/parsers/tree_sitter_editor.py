from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Sequence
import logging

from GithubAnalyzer.models.core.errors import ParserError

from ....utils.logging.tree_sitter_logging import TreeSitterLogHandler
from .tree_sitter_traversal import TreeSitterTraversal
"""Tree-sitter editor for handling incremental parsing and tree updates."""
from dataclasses import dataclass
from tree_sitter import Tree, Node, Point, Parser, Range, Query, Language
import sys

from GithubAnalyzer.utils.logging.logging_config import get_logger
from .tree_sitter_query import TreeSitterQueryHandler
from tree_sitter_language_pack import get_binding, get_language, get_parser

logger = get_logger(__name__)

@dataclass
class EditOperation:
    """Represents a single edit operation on a tree."""
    old_text: str
    new_text: str
    start_position: Point
    end_position: Point
    start_byte: int
    end_byte: int

class TreeSitterEditor:
    """Handles tree editing and incremental parsing."""

    def __init__(self):
        """Initialize editor with traversal and query utilities."""
        self._traversal = TreeSitterTraversal()
        self._log_handler = TreeSitterLogHandler('tree_sitter')
        self._query_handler = TreeSitterQueryHandler(self._log_handler)
        
        # Initialize language and parser
        self._language = get_language("python")
        self._parser = get_parser("python")
        
        # Enable logging by default for any parsers we create/use
        self.enable_parser_logging(self._parser)

    def __del__(self):
        """Clean up logging when editor is destroyed."""
        if hasattr(self, '_parser'):
            self.disable_parser_logging(self._parser)

    def enable_parser_logging(self, parser: Parser) -> None:
        """Enable logging for a parser."""
        if not parser.logger:
            def log_function(log_type: int, msg: str) -> None:
                """Wrapper function to handle parser logging."""
                record = logging.LogRecord(
                    name="tree_sitter",
                    level=logging.DEBUG,
                    pathname="",
                    lineno=0,
                    msg=msg,
                    args=(),
                    exc_info=None
                )
                self._log_handler.emit(record)
            parser.logger = log_function

    def disable_parser_logging(self, parser: Parser) -> None:
        """Disable logging for a parser."""
        if parser.logger:
            parser.logger = None

    def parse_code(self, code: str) -> Tree:
        """Parse Python code into a tree-sitter Tree.
        
        Args:
            code: Python code to parse
            
        Returns:
            Tree-sitter Tree representing the parsed code
            
        Raises:
            ParserError: If parsing fails
        """
        encoded_code = code.encode('utf8')
        tree = self._parser.parse(encoded_code)
        
        if not isinstance(tree, Tree):
            raise ParserError("Failed to create parse tree")
            
        # Check for syntax errors
        if tree.root_node.has_error:
            error_nodes = [
                node for node in tree.root_node.children 
                if node.has_error or node.type == 'ERROR'
            ]
            if error_nodes:
                error_msg = "Syntax errors found:\n"
                for node in error_nodes:
                    error_msg += f"- ERROR at line {node.start_point[0] + 1}: {node.type}\n"
                raise ParserError(error_msg)
                
        return tree

    def get_changed_ranges(self, old_tree: Tree, new_tree: Tree) -> List[Range]:
        """Get ranges that changed between two trees.
        
        Args:
            old_tree: Previous version of tree
            new_tree: New version of tree
            
        Returns:
            List of changed ranges
        """
        return old_tree.changed_ranges(new_tree)

    def visualize_tree(self, tree: Tree, output_path: Optional[Union[str, Path]] = None) -> str:
        """Get a string visualization of the tree.
        
        Args:
            tree: Tree to visualize
            output_path: Optional path to save visualization to
            
        Returns:
            String representation of tree
        """
        def _node_to_str(node: Node, level: int = 0) -> str:
            # Get node type and any text content
            result = "  " * level + f"({node.type}"
            
            # Add text content if it's a leaf node
            if len(node.children) == 0:
                text = node.text.decode('utf8').strip()
                if text:
                    result += f' "{text}"'
            
            # Add children recursively
            if node.children:
                result += "\n"
                for child in node.children:
                    result += _node_to_str(child, level + 1) + "\n"
                result += "  " * level
            
            result += ")"
            return result
            
        visualization = _node_to_str(tree.root_node)
        
        if output_path:
            try:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(visualization)
            except Exception as e:
                self._log_handler.error(f"Failed to write visualization to {output_path}: {e}")
                
        return visualization

    def is_valid_position(self, tree: Tree, position: Point) -> bool:
        """Check if a position is valid in the tree.
        
        Args:
            tree: Tree to check position in
            position: Position to validate
            
        Returns:
            True if position is valid
        """
        return self._traversal.is_valid_position(tree.root_node, position)

    def create_edit_operation(self, tree: Tree, start_position: Point, end_position: Point, new_text: str) -> EditOperation:
        """Create an edit operation.
        
        Args:
            tree: Tree to create edit for
            start_position: Start position of edit
            end_position: End position of edit
            new_text: New text to insert
            
        Returns:
            EditOperation object
            
        Raises:
            ParserError: If positions are invalid
        """
        details = {
            "tree_type": tree.root_node.type if tree and tree.root_node else None,
            "start_position": str(start_position),
            "end_position": str(end_position),
            "new_text_length": len(new_text)
        }
        
        if not self.verify_edit_position(tree, start_position, end_position):
            self._log_handler.error({
                "message": "Invalid edit positions",
                "context": details
            })
            raise ParserError(
                message="Invalid edit positions",
                details=str(details)
            )
            
        try:
            # Get old text
            old_text = self._get_text_between_positions(tree, start_position, end_position)
            
            # Calculate byte offsets
            start_byte = self._calculate_byte_offset(tree, start_position)
            end_byte = start_byte + len(old_text.encode('utf8'))
            
            return EditOperation(
                old_text=old_text,
                new_text=new_text,
                start_position=start_position,
                end_position=end_position,
                start_byte=start_byte,
                end_byte=end_byte
            )
        except Exception as e:
            error_details = {**details, "error": str(e)}
            self._log_handler.error({
                "message": "Failed to create edit operation",
                "context": error_details
            })
            raise ParserError(
                message=f"Failed to create edit operation: {e}",
                details=str(error_details)
            )

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

    def verify_tree_changes(self, tree: Tree) -> bool:
        """Verify if a tree has valid changes."""
        if not tree or not tree.root_node:
            return False
            
        return self._query_handler.is_valid_node(tree.root_node)

    def verify_edit_position(self, tree: Tree, start: Point, end: Point) -> bool:
        """Verify if an edit position is valid."""
        if not tree or not tree.root_node:
            return False
        
        # Get text and split into lines
        text = tree.root_node.text.decode('utf8')
        lines = text.split('\n')
        
        # Check if start position is valid
        if start.row < 0 or start.row >= len(lines):
            return False
        if start.column < 0 or start.column > len(lines[start.row]):
            return False
            
        # Check if end position is valid
        # End position can be at start of a new line that doesn't exist yet
        if end.row < 0 or end.row > len(lines):
            return False
        if end.row < len(lines) and (end.column < 0 or end.column > len(lines[end.row])):
            return False
            
        # Check if start comes before end
        if start.row > end.row or (start.row == end.row and start.column > end.column):
            return False
            
        return True

    def apply_edit(self, tree: Tree, edit: EditOperation) -> None:
        """Apply an edit operation to a tree.
        
        Args:
            tree: Tree to edit
            edit: Edit operation to apply
            
        Raises:
            ParserError: If the tree is invalid or edit is invalid
        """
        details = {
            "tree_type": tree.root_node.type if tree and tree.root_node else None,
            "edit": {
                "old_text": edit.old_text,
                "new_text": edit.new_text,
                "start_position": str(edit.start_position),
                "end_position": str(edit.end_position)
            }
        }
        
        if not self._validate_tree(tree, "apply_edit"):
            self._log_handler.error({
                "message": "Cannot apply edit to invalid tree",
                "context": details
            })
            raise ParserError(
                message="Cannot apply edit to invalid tree",
                details=str(details)
            )
            
        self._log_handler.info({
            "message": "Applying edit",
            "context": details
        })
        
        try:
            tree.edit(
                start_byte=edit.start_byte,
                old_end_byte=edit.end_byte,
                new_end_byte=edit.start_byte + len(edit.new_text.encode()),
                start_point=edit.start_position,
                old_end_point=edit.end_position,
                new_end_point=self._calculate_new_end_point(
                    edit.start_position,
                    edit.new_text
                )
            )
        except Exception as e:
            error_details = {**details, "error": str(e)}
            self._log_handler.error({
                "message": "Failed to apply edit",
                "context": error_details
            })
            raise ParserError(
                message=f"Failed to apply edit: {e}",
                details=str(error_details)
            )

    def validate_tree(self, tree: Tree) -> bool:
        """Validate a tree."""
        return self._validate_tree(tree)

    def update_tree(self, tree: Tree, edits: List[EditOperation], parser: Parser) -> Optional[Tree]:
        """Update a tree with edits using incremental parsing."""
        if not self._validate_tree(tree, "update"):
            self._log_handler.error("Cannot update invalid tree")
            return None

        try:
            import time
            start_time = time.time()
            
            # Apply edits
            self._log_handler.info({
                "message": "Applying edits to tree",
                "context": {
                    "edit_count": len(edits),
                    "tree_node_count": tree.root_node.child_count
                }
            })
            
            # Build new source by applying edits
            source_bytes = bytearray(tree.root_node.text)
            self._log_handler.debug({
                "message": "Initial source state",
                "context": {
                    "source_length": len(source_bytes),
                    "tree_error_count": sum(1 for _ in tree.root_node.children_by_field_name('error'))
                }
            })
            
            # Apply edits in reverse order to maintain byte offsets
            for edit in reversed(edits):
                edit_start = time.time()
                self._log_handler.debug({
                    "message": "Applying edit",
                    "context": {
                        "old_text": edit.old_text,
                        "new_text": edit.new_text,
                        "start_position": edit.start_position,
                        "end_position": edit.end_position
                    }
                })
                
                start_byte = self._get_byte_offset(tree, edit.start_position)
                end_byte = (self._get_byte_offset(tree, edit.end_position) 
                          if edit.end_position 
                          else start_byte + len(edit.old_text.encode('utf8')))
                
                # Replace bytes in source
                new_bytes = edit.new_text.encode('utf8')
                source_bytes[start_byte:end_byte] = new_bytes
                
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
                
                edit_duration = (time.time() - edit_start) * 1000
                self._log_handler.debug({
                    "message": "Edit applied",
                    "context": {
                        "duration_ms": edit_duration,
                        "new_source_length": len(source_bytes)
                    }
                })

            # Reparse with timeout
            self._log_handler.debug({
                "message": "Reparsing tree",
                "context": {
                    "timeout_micros": parser.timeout_micros,
                    "source_length": len(source_bytes)
                }
            })
            
            parse_start = time.time()
            parser.reset()  # Reset parser state
            parser.timeout_micros = 100000  # 100ms timeout
            new_tree = parser.parse(bytes(source_bytes), tree)
            parse_duration = (time.time() - parse_start) * 1000

            if not new_tree or not new_tree.root_node:
                self._log_handler.error({
                    "message": "Parser produced invalid tree",
                    "context": {
                        "duration_ms": parse_duration,
                        "tree": None if not new_tree else "No root node"
                    }
                })
                raise ParserError("Parser failed to produce valid tree")

            total_duration = (time.time() - start_time) * 1000
            self._log_handler.info({
                "message": "Tree updated successfully",
                "context": {
                    "total_duration_ms": total_duration,
                    "parse_duration_ms": parse_duration,
                    "new_node_count": new_tree.root_node.child_count,
                    "has_errors": new_tree.root_node.has_error
                }
            })
            
            return new_tree
            
        except Exception as e:
            self._log_handler.error({
                "message": "Failed to update tree",
                "context": {
                    "error": str(e),
                    "edit_count": len(edits)
                }
            })
            raise ParserError(f"Failed to update tree: {e}")

    def reparse_tree(self, parser: Parser, tree: Tree) -> Tree:
        """Reparse a tree after edits.

        Args:
            parser: The parser to use
            tree: The tree to reparse

        Returns:
            Tree: The reparsed tree

        Raises:
            ParserError: If the tree is invalid
        """
        if not self._validate_tree(tree, "reparse"):
            raise ParserError("Cannot reparse invalid tree")

        try:
            text = tree.root_node.text
            if isinstance(text, str):
                text = text.encode('utf8')
            elif not isinstance(text, bytes):
                text = bytes(str(text), 'utf8')
            return parser.parse(text)
        except Exception as e:
            raise ParserError(f"Failed to reparse tree: {e}")

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

    def _get_text_between_positions(self, tree: Tree, start: Point, end: Point) -> str:
        """Get text between two positions."""
        if not tree or not tree.root_node:
            raise ParserError("Cannot get text between positions: Invalid tree")
            
        try:
            text = tree.root_node.text.decode('utf8')
            lines = text.split('\n')
            
            # Handle end-of-file positions
            if start.row >= len(lines):
                return ""
                
            if end.row >= len(lines):
                if start.row == len(lines) - 1:
                    return lines[start.row][start.column:]
                return ""
                
            # Handle single line case
            if start.row == end.row:
                line = lines[start.row]
                end_col = min(end.column, len(line))
                return line[start.column:end_col]
                
            # Handle multi-line case
            result = [lines[start.row][start.column:]]
            for i in range(start.row + 1, min(end.row, len(lines))):
                result.append(lines[i])
            if end.row < len(lines):
                result.append(lines[end.row][:end.column])
            return '\n'.join(result)
            
        except Exception as e:
            raise ParserError(f"Failed to get text between positions: {str(e)}")

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