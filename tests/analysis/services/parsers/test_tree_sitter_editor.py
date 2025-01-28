"""Tests for TreeSitterEditor."""
import pytest
import logging
from pathlib import Path
from tree_sitter import Tree, Node, Point
from tree_sitter_language_pack import get_parser, get_language

from GithubAnalyzer.services.analysis.parsers.tree_sitter_editor import TreeSitterEditor
from GithubAnalyzer.utils.logging.tree_sitter_logging import TreeSitterLogHandler
from GithubAnalyzer.utils.logging.logging_config import configure_logging

@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for all tests."""
    configure_logging(level=logging.DEBUG, structured=True, enable_tree_sitter=True)
    root_logger = logging.getLogger('tree_sitter')
    if not any(isinstance(h, TreeSitterLogHandler) for h in root_logger.handlers):
        handler = TreeSitterLogHandler()
        root_logger.addHandler(handler)
    yield
    # Clean up handlers after test
    root_logger.handlers.clear()

@pytest.fixture
def editor():
    """Create a TreeSitterEditor instance."""
    return TreeSitterEditor()

@pytest.fixture
def python_parser():
    """Get a Python parser."""
    return get_parser("python")

@pytest.fixture
def python_tree(python_parser):
    """Create a Python tree."""
    code = "def test(): pass"
    return python_parser.parse(bytes(code, "utf8"))

def test_parse_code(editor):
    """Test parsing Python code."""
    code = "def test(): pass"
    tree = editor.parse_code(code)
    assert isinstance(tree, Tree)
    assert tree.root_node.type == "module"

def test_get_changed_ranges(editor):
    """Test getting changed ranges between trees."""
    old_code = "def test(): pass"
    new_code = "def test(): return True"
    
    old_tree = editor.parse_code(old_code)
    new_tree = editor.parse_code(new_code)
    
    ranges = editor.get_changed_ranges(old_tree, new_tree)
    assert len(ranges) > 0

def test_update_tree_with_edits(editor):
    """Test updating a tree with edits."""
    # Initial code and tree
    code = "def test(): pass"
    tree = editor.parse_code(code)
    
    # Create edit operation
    start_point = Point(0, 12)  # After 'def test():'
    end_point = Point(0, 16)  # End of 'pass'
    new_text = "\n    return True"
    
    # Calculate byte offsets
    start_byte = len("def test():".encode('utf8'))
    old_end_byte = len(code.encode('utf8'))
    new_end_byte = start_byte + len(new_text.encode('utf8'))
    
    # First apply the edit to the tree to keep it in sync
    tree.edit(
        start_byte=start_byte,
        old_end_byte=old_end_byte,
        new_end_byte=new_end_byte,
        start_point=start_point,
        old_end_point=end_point,
        new_end_point=Point(1, 14)  # After "\n    return True"
    )
    
    # Then parse with the new text
    new_code = code[:start_byte] + new_text
    updated_tree = editor.parse_code(new_code)
    
    # Verify the result
    assert isinstance(updated_tree, Tree)
    assert not updated_tree.root_node.has_error
    assert updated_tree.root_node.text.decode('utf8') == new_code

def test_visualize_tree(editor, tmp_path):
    """Test visualizing a tree."""
    code = "def test(): pass"
    tree = editor.parse_code(code)
    
    # Test visualization without output path
    visualization = editor.visualize_tree(tree)
    assert isinstance(visualization, str)
    assert "module" in visualization
    
    # Test visualization with output path
    output_path = tmp_path / "tree.txt"
    visualization = editor.visualize_tree(tree, output_path)
    assert output_path.exists()
    assert isinstance(visualization, str)

def test_is_valid_position(editor):
    """Test position validation."""
    code = "def test():\n    pass"
    tree = editor.parse_code(code)
    
    # Test valid positions
    assert editor.is_valid_position(tree.root_node, Point(0, 0))  # Start of file
    assert editor.is_valid_position(tree.root_node, Point(0, 11))  # End of first line
    assert editor.is_valid_position(tree.root_node, Point(1, 4))  # Indented 'pass'
    
    # Test invalid positions
    assert not editor.is_valid_position(tree.root_node, Point(-1, 0))  # Negative row
    assert not editor.is_valid_position(tree.root_node, Point(0, -1))  # Negative column
    assert not editor.is_valid_position(tree.root_node, Point(2, 0))  # Past end of file

def test_create_edit_operation(editor):
    """Test creating an edit operation."""
    code = "def test(): pass"
    tree = editor.parse_code(code)
    
    start_point = Point(0, 12)  # After 'def test(): '
    end_point = Point(0, 16)  # End of 'pass'
    new_text = "\n    return True"
    
    edit = editor.create_edit_operation(tree, start_point, end_point, new_text)
    
    # Verify the edit operation has all required fields for Tree.edit()
    assert edit.start_byte == len("def test(): ".encode('utf8'))  # Include space after colon
    assert edit.old_end_byte == len(code.encode('utf8'))
    assert edit.new_end_byte == edit.start_byte + len(new_text.encode('utf8'))
    assert edit.start_point == start_point
    assert edit.old_end_point == end_point
    assert edit.new_end_point == Point(1, 14)  # After "\n    return True"

def test_structured_logging(editor, caplog):
    """Test structured logging output."""
    with caplog.at_level(logging.DEBUG, logger='tree_sitter'):
        code = "def test(): pass"
        tree = editor.parse_code(code)
        assert tree is not None
        assert all(isinstance(record.msg, dict) for record in caplog.records)