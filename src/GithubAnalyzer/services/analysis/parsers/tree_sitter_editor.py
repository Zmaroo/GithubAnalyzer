"""Tree-sitter editor for code manipulation."""
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict

from tree_sitter import Language, Node, Parser, Point, Query, Range, Tree

from GithubAnalyzer.models.analysis.types import NodeDict, NodeList
from GithubAnalyzer.models.analysis.query import QueryResult
from GithubAnalyzer.models.core.errors import EditorError, ParserError
from GithubAnalyzer.models.core.tree_sitter_core import (
    get_node_text, get_node_text_safe, get_node_type, is_valid_node, node_to_dict
)
from GithubAnalyzer.services.core.base_service import BaseService
from GithubAnalyzer.services.parsers.core.query_handler import TreeSitterQueryHandler
from GithubAnalyzer.utils.logging import get_logger

from .language_service import LanguageService
from .traversal_service import TraversalService

# Initialize logger
logger = get_logger(__name__)

@dataclass
class EditOperation:
    """Represents an edit operation on a tree."""
    old_text: str
    new_text: str
    start_position: Point
    end_position: Point
    start_byte: int
    old_end_byte: int
    new_end_byte: int
    start_point: Point
    old_end_point: Point
    new_end_point: Point
    text: str

@dataclass
class TreeSitterEditor(BaseService):
    """Editor for manipulating code using tree-sitter."""
    
    _language_service: LanguageService = field(default_factory=LanguageService)
    _traversal_service: TraversalService = field(default_factory=TraversalService)
    _query_handler: TreeSitterQueryHandler = field(default_factory=TreeSitterQueryHandler)
    _parser: Optional[Parser] = field(default=None)
    _text: str = field(default="")
    _log_handler: Any = field(default_factory=lambda: logger)
    _operation_times: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    
    def __post_init__(self):
        """Initialize editor."""
        super().__post_init__()
        
        self._log("debug", "Tree-sitter editor initialized",
                operation="initialization")
        
    def parse_code(self, code: str, language: str) -> Tree:
        """Parse code into a syntax tree.
        
        Args:
            code: The code to parse
            language: The language of the code
            
        Returns:
            Parsed syntax tree
            
        Raises:
            EditorError: If parsing fails
        """
        self._log("debug", "Parsing code",
                operation="code_parsing",
                language=language,
                code_length=len(code))
                
        try:
            # Get parser for language
            parser = self._language_service.get_parser(language)
            
            # Parse code
            tree = parser.parse(bytes(code, "utf8"))
            if not tree:
                raise EditorError(f"Failed to parse {language} code")
                
            self._log("debug", "Code parsed successfully",
                    operation="code_parsing",
                    language=language,
                    root_type=tree.root_node.type)
                    
            return tree
            
        except Exception as e:
            self._log("error", "Code parsing failed",
                    operation="code_parsing",
                    language=language,
                    error=str(e))
            raise EditorError(f"Failed to parse code: {str(e)}")
            
    def edit_code(self, tree: Tree, edits: List[Dict[str, Any]]) -> str:
        """Apply edits to code using the syntax tree.
        
        Args:
            tree: The syntax tree to edit
            edits: List of edit operations to apply
            
        Returns:
            The edited code
            
        Raises:
            EditorError: If editing fails
        """
        self._log("debug", "Applying code edits",
                operation="code_editing",
                edit_count=len(edits))
                
        try:
            # Apply each edit
            for edit in edits:
                edit_type = edit.get('type')
                if not edit_type:
                    continue
                    
                if edit_type == 'replace':
                    self._replace_node(tree, edit)
                elif edit_type == 'insert':
                    self._insert_node(tree, edit)
                elif edit_type == 'delete':
                    self._delete_node(tree, edit)
                    
            # Get edited code
            edited_code = self._get_edited_code(tree)
            
            self._log("debug", "Code edits applied successfully",
                    operation="code_editing",
                    edit_count=len(edits))
                    
            return edited_code
            
        except Exception as e:
            self._log("error", "Code editing failed",
                    operation="code_editing",
                    error=str(e))
            raise EditorError(f"Failed to edit code: {str(e)}")

    def get_changed_ranges(self, old_tree: Tree, new_tree: Tree) -> List[Range]:
        """Get ranges that changed between two trees.
        
        Args:
            old_tree: Previous version of tree
            new_tree: New version of tree
            
        Returns:
            List of changed ranges
        """
        start_time = self._time_operation('get_changed_ranges')
        try:
            return old_tree.changed_ranges(new_tree)
        finally:
            self._end_operation('get_changed_ranges', start_time)

    def visualize_tree(self, tree: Tree, output_path: Optional[Union[str, Path]] = None) -> str:
        """Get a string visualization of the tree.
        
        Args:
            tree: Tree to visualize
            output_path: Optional path to save visualization to
            
        Returns:
            String representation of tree
        """
        start_time = self._time_operation('visualize_tree')
        try:
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
                    self._logger.error(f"Failed to write visualization to {output_path}: {e}")
                    
            return visualization
        finally:
            self._end_operation('visualize_tree', start_time)

    def is_valid_position(self, tree: Node, position: Point, end_position: Optional[Point] = None) -> bool:
        """Check if position(s) are valid in the tree."""
        start_time = self._time_operation('is_valid_position')
        try:
            _, lines = self._get_safe_text(tree)
            
            # Basic bounds checking for start position
            if position.row < 0 or position.row >= len(lines):
                return False
            if position.column < 0 or position.column > len(lines[position.row]):
                return False
                
            # If end position provided, check it too
            if end_position:
                if end_position.row < 0 or end_position.row >= len(lines):
                    return False
                if end_position.column < 0 or end_position.column > len(lines[end_position.row]):
                    return False
                    
                # Check if start comes before end
                if position.row > end_position.row or (position.row == end_position.row and position.column > end_position.column):
                    return False
                    
            return True
        finally:
            self._end_operation('is_valid_position', start_time)

    def create_edit_operation(self, tree: Tree, start_position: Point, end_position: Point, new_text: str) -> EditOperation:
        """Create an edit operation for a tree."""
        if not self.is_valid_position(tree.root_node, start_position, end_position):
            raise ValueError(f"Invalid edit positions: {start_position} -> {end_position}")
            
        # Get text and convert positions to byte offsets
        self._text = tree.root_node.text.decode('utf8')
        text = self._text
        
        # Log the exact text content and character positions
        self._logger.debug({
            "message": "Text analysis for byte calculations",
            "context": {
                'source': 'tree-sitter',
                'type': 'editor',
                'log_type': 'edit_analysis',
                "full_text": text,
                "text_length": len(text),
                "text_bytes": len(text.encode('utf8')),
                "text_chars": [{"index": i, "char": c, "bytes": len(c.encode('utf8'))} for i, c in enumerate(text)],
                "start_position": {
                    "row": start_position.row,
                    "column": start_position.column,
                    "text_before": text[:start_position.column],
                    "text_before_bytes": len(text[:start_position.column].encode('utf8'))
                }
            }
        })
        
        # Calculate byte offsets directly from the text
        lines = text.split('\n')
        
        # Log line-by-line analysis
        self._logger.debug({
            "message": "Line-by-line analysis",
            "context": {
                "lines": [{
                    "index": i,
                    "content": line,
                    "length": len(line),
                    "bytes": len(line.encode('utf8')),
                    "with_newline_bytes": len(line.encode('utf8')) + 1
                } for i, line in enumerate(lines)]
            }
        })
        
        # Calculate byte offsets
        start_byte = 0
        for i in range(start_position.row):
            start_byte += len(lines[i].encode('utf8')) + 1  # +1 for newline
        start_byte += len(lines[start_position.row][:start_position.column].encode('utf8'))
        
        end_byte = 0
        for i in range(end_position.row):
            end_byte += len(lines[i].encode('utf8')) + 1  # +1 for newline
        end_byte += len(lines[end_position.row][:end_position.column].encode('utf8'))
        
        # Log byte offset calculations
        self._logger.debug({
            "message": "Byte offset calculations",
            "context": {
                "start_byte": {
                    "total": start_byte,
                    "previous_lines_bytes": sum(len(line.encode('utf8')) + 1 for line in lines[:start_position.row]),
                    "current_line_bytes": len(lines[start_position.row][:start_position.column].encode('utf8')),
                    "text_at_position": lines[start_position.row][start_position.column-1:start_position.column+1] if start_position.column > 0 else ""
                },
                "end_byte": {
                    "total": end_byte,
                    "previous_lines_bytes": sum(len(line.encode('utf8')) + 1 for line in lines[:end_position.row]),
                    "current_line_bytes": len(lines[end_position.row][:end_position.column].encode('utf8')),
                    "text_at_position": lines[end_position.row][end_position.column-1:end_position.column+1] if end_position.column > 0 else ""
                }
            }
        })
        
        # Get nodes at byte positions
        start_node = tree.root_node.descendant_for_byte_range(start_byte, start_byte + 1)
        end_node = tree.root_node.descendant_for_byte_range(end_byte - 1, end_byte)
        
        if not start_node or not end_node:
            raise ValueError("Could not find nodes at edit positions")
            
        # Calculate new end byte
        new_end_byte = start_byte + len(new_text.encode('utf8'))
        
        # Get old text between positions using byte offsets
        old_text = text[start_byte:end_byte]
        
        # Calculate new end point
        new_end_point = self._calculate_new_end_point(start_position, new_text)
        
        # Create the edit operation
        edit = EditOperation(
            old_text=old_text,
            new_text=new_text,
            start_position=start_position,
            end_position=end_position,
            start_byte=start_byte,
            old_end_byte=end_byte,
            new_end_byte=new_end_byte,
            start_point=start_position,
            old_end_point=end_position,
            new_end_point=new_end_point,
            text=text
        )
        
        # Log detailed byte range information
        self._logger.debug({
            "message": "Creating edit operation",
            "context": {
                "start_node": {
                    "type": start_node.type,
                    "text": start_node.text.decode('utf8'),
                    "start_byte": start_node.start_byte,
                    "end_byte": start_node.end_byte,
                    "start_point": f"({start_node.start_point[0]}, {start_node.start_point[1]})",
                    "end_point": f"({start_node.end_point[0]}, {start_node.end_point[1]})"
                },
                "end_node": {
                    "type": end_node.type,
                    "text": end_node.text.decode('utf8'),
                    "start_byte": end_node.start_byte,
                    "end_byte": end_node.end_byte,
                    "start_point": f"({end_node.start_point[0]}, {end_node.start_point[1]})",
                    "end_point": f"({end_node.end_point[0]}, {end_node.end_point[1]})"
                },
                "edit": {
                    "start_position": f"({start_position.row}, {start_position.column})",
                    "end_position": f"({end_position.row}, {end_position.column})",
                    "old_text": old_text,
                    "new_text": new_text,
                    "start_byte": start_byte,
                    "old_end_byte": end_byte,
                    "new_end_byte": new_end_byte
                }
            }
        })
        
        return edit

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
        # Reuse is_valid_position for basic bounds checking
        if not self.is_valid_position(tree.root_node, start, end):
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
                old_end_byte=edit.old_end_byte,
                new_end_byte=edit.new_end_byte,
                start_point=edit.start_point,
                old_end_point=edit.old_end_point,
                new_end_point=edit.new_end_point
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

    def update_tree(self, tree: Tree, edits: Union[EditOperation, List[EditOperation]]) -> Tree:
        """Update a tree with edits."""
        start_time = self._time_operation('update_tree')
        try:
            if not self._validate_tree(tree):
                raise ParserError("Cannot update invalid tree")

            # Convert single edit to list
            edit_list = [edits] if isinstance(edits, EditOperation) else edits
            
            # Apply edits to the tree
            for edit in edit_list:
                try:
                    tree.edit(
                        start_byte=edit.start_byte,
                        old_end_byte=edit.old_end_byte,
                        new_end_byte=edit.new_end_byte,
                        start_point=edit.start_point,
                        old_end_point=edit.old_end_point,
                        new_end_point=edit.new_end_point
                    )
                except Exception as e:
                    raise ParserError(f"Failed to apply edit: {e}")

            # Update text and reparse
            text = self._text
            new_tree = self._parser.parse(text.encode('utf-8'))
            if not self._validate_tree(new_tree):
                raise ParserError("Failed to reparse tree after edits")
                
            return new_tree
        finally:
            self._end_operation('update_tree', start_time)

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

    def _calculate_new_end_point(self, start: Point, text: str) -> Point:
        """Calculate end point after inserting text.
        
        Args:
            start: Start position
            text: Text to insert
            
        Returns:
            New end position
        """
        lines = text.split('\n')
        if len(lines) == 1:
            return Point(start.row, start.column + len(text))
        else:
            # For multi-line edits, we need to handle the last line's length correctly
            # The column should be the length of the last line
            return Point(
                start.row + len(lines) - 1,
                len(lines[-1]) - 1 if len(lines) > 1 else start.column + len(lines[-1])
            )

    def _get_text_between_positions(self, tree: Tree, start: Point, end: Point) -> str:
        """Get text between two positions."""
        _, lines = self._get_safe_text(tree)
        
        if start.row >= len(lines):
            return ""
            
        if end.row >= len(lines):
            if start.row == len(lines) - 1:
                return lines[start.row][start.column:]
            return ""
            
        if start.row == end.row:
            line = lines[start.row]
            end_col = min(end.column, len(line))
            return line[start.column:end_col]
            
        result = [lines[start.row][start.column:]]
        for i in range(start.row + 1, min(end.row, len(lines))):
            result.append(lines[i])
        if end.row < len(lines):
            result.append(lines[end.row][:end.column])
        return '\n'.join(result)

    def _validate_tree(self, tree: Union[Tree, Node], context: str = "") -> bool:
        """Validate a tree or node."""
        if not tree:
            return False
        if isinstance(tree, Tree) and not tree.root_node:
            return False
        return True

    def update_tree_with_edits(self, tree: Tree, edits: List[EditOperation]) -> Tree:
        """Update a tree with edits.
        
        Args:
            tree: Tree to update
            edits: List of edits to apply
            
        Returns:
            Updated tree
            
        Raises:
            ParserError: If update fails
        """
        start_time = self._time_operation('update_tree_with_edits')
        try:
            # Apply edits to the tree
            for edit in edits:
                tree.edit(
                    start_byte=edit.start_byte,
                    old_end_byte=edit.old_end_byte,
                    new_end_byte=edit.new_end_byte,
                    start_point=edit.start_point,
                    old_end_point=edit.old_end_point,
                    new_end_point=edit.new_end_point
                )
                
            # Get the updated text by applying the edits
            text = self._get_text_with_edits(tree.root_node.text.decode('utf8'), edits)

            # Reparse tree with the updated text
            new_tree = self._parser.parse(text.encode('utf-8'))
            if not self._validate_tree(new_tree):
                raise ParserError("Failed to reparse tree after edits")
                
            return new_tree
            
        except Exception as e:
            raise ParserError(f"Failed to update tree with edits: {e}")
        finally:
            self._end_operation('update_tree_with_edits', start_time)

    def _get_text_with_edits(self, text: str, edits: List[EditOperation]) -> str:
        """Get text with edits applied.
        
        Args:
            text: Original text
            edits: List of edits to apply
            
        Returns:
            Updated text
        """
        # Sort edits by start byte in reverse order to apply from end to start
        sorted_edits = sorted(edits, key=lambda x: x.start_byte, reverse=True)

        # Apply each edit to the text
        for edit in sorted_edits:
            text = text[:edit.start_byte] + edit.new_text + text[edit.old_end_byte:]

        return text

    def _time_operation(self, operation_name: str) -> float:
        """Start timing an operation."""
        start_time = time.time()
        if operation_name not in self._operation_times:
            self._operation_times[operation_name] = []
        return start_time

    def _end_operation(self, operation_name: str, start_time: float) -> None:
        """End timing for an operation."""
        duration = (time.time() - start_time) * 1000
        self._operation_times[operation_name].append(duration)
        
        times = self._operation_times[operation_name]
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        self._logger.debug({
            "message": f"Operation timing: {operation_name}",
            "context": {
                "operation": operation_name,
                "duration_ms": duration,
                "avg_duration_ms": avg_time,
                "max_duration_ms": max_time,
                "call_count": len(times)
            }
        })

    def _get_safe_text(self, tree: Union[Tree, Node]) -> Tuple[str, List[str]]:
        """Get text and lines from tree/node."""
        if not self._validate_tree(tree):
            raise ValueError("Invalid tree or node")
        
        if isinstance(tree, Tree):
            text = self._text
        else:
            text = tree.text.decode("utf8")
        lines = text.split("\n")
        return text, lines

    def find_nodes_by_type(self, tree: Tree, node_type: str, language: Optional[str] = None) -> List[Node]:
        """Find nodes of a specific type in the tree.
        
        Args:
            tree: Tree to search
            node_type: Type of nodes to find
            language: Optional language override
            
        Returns:
            List of matching nodes
        """
        return self._query_handler.find_nodes_by_type(tree.root_node, node_type, language)

    def find_nodes_by_pattern(self, tree: Tree, pattern_type: str, language: Optional[str] = None) -> List[Dict[str, Node]]:
        """Find nodes matching a pattern in the tree.
        
        Args:
            tree: Tree to search
            pattern_type: Type of pattern to match
            language: Optional language override
            
        Returns:
            List of matching nodes with captures
        """
        return self._query_handler.find_nodes(tree.root_node, pattern_type, language)

    def validate_syntax(self, tree: Tree, language: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Validate syntax of a tree.
        
        Args:
            tree: Tree to validate
            language: Optional language override
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        return self._query_handler.validate_syntax(tree.root_node, language)

    def find_error_nodes(self, tree: Tree) -> List[Node]:
        """Find error nodes in a tree.
        
        Args:
            tree: Tree to search
            
        Returns:
            List of error nodes
        """
        return self._query_handler.find_error_nodes(tree.root_node)

    def find_missing_nodes(self, tree: Tree) -> List[Node]:
        """Find missing nodes in a tree.
        
        Args:
            tree: Tree to search
            
        Returns:
            List of missing nodes
        """
        return self._query_handler.find_missing_nodes(tree.root_node)

    def execute_query(self, tree: Tree, query_string: str, language: Optional[str] = None) -> QueryResult:
        """Execute a query on a tree.
        
        Args:
            tree: Tree to query
            query_string: Query pattern to execute
            language: Optional language override
            
        Returns:
            Query execution result
        """
        query = self._query_handler.create_query(query_string, language)
        if not query:
            return QueryResult(is_valid=False, errors=["Failed to create query"])
            
        return self._query_handler.execute_query(query, tree)