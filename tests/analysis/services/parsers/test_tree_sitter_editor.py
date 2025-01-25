"""Tests for TreeSitterEditor."""
import pytest
from unittest.mock import patch, Mock
import logging
from tree_sitter import Tree, Parser, Point
from tree_sitter_language_pack import get_parser

from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_editor import (
    TreeSitterEditor,
    EditOperation,
    ParserError
)
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_logging import TreeSitterLogHandler

@pytest.fixture
def editor():
    """Create a TreeSitterEditor instance."""
    return TreeSitterEditor()

@pytest.fixture
def python_parser():
    """Create a Python parser."""
    return get_parser("python")

@pytest.fixture
def simple_tree(python_parser):
    """Create a simple Python AST."""
    code = "def test(): pass"
    return python_parser.parse(bytes(code, "utf8"))

def test_enable_disable_parser_logging(editor, python_parser):
    """Test enabling and disabling parser logging."""
    # Enable logging
    editor.enable_parser_logging(python_parser)
    assert hasattr(python_parser, "logger")
    assert python_parser.logger is not None

    # Disable logging
    editor.disable_parser_logging(python_parser)
    assert python_parser.logger is None

def test_get_changed_ranges(editor, python_parser):
    """Test getting changed ranges between trees."""
    old_code = "def test(): pass"
    new_code = "def test(): return 42"
    
    old_tree = python_parser.parse(bytes(old_code, "utf8"))
    new_tree = python_parser.parse(bytes(new_code, "utf8"))
    
    ranges = editor.get_changed_ranges(old_tree, new_tree)
    assert len(ranges) > 0

def test_visualize_tree(editor, simple_tree, tmp_path):
    """Test tree visualization."""
    output_path = tmp_path / "tree.dot"
    success = editor.visualize_tree(simple_tree, output_path)
    assert success
    assert output_path.exists()

def test_is_valid_position(editor, simple_tree):
    """Test position validation."""
    # Valid positions
    assert editor.is_valid_position(simple_tree, Point(0, 0))
    assert editor.is_valid_position(simple_tree, Point(0, 10))
    
    # Invalid positions
    assert not editor.is_valid_position(simple_tree, Point(-1, 0))
    assert not editor.is_valid_position(simple_tree, Point(100, 0))

def test_create_edit_operation(editor, simple_tree):
    """Test creating edit operation."""
    edit = editor.create_edit_operation(
        simple_tree,
        old_text="pass",
        new_text="return 42",
        start_position=Point(0, 12)
    )
    
    assert isinstance(edit, EditOperation)
    assert edit.old_text == "pass"
    assert edit.new_text == "return 42"

def test_apply_edit(editor, simple_tree):
    """Test applying edit operation."""
    edit = editor.create_edit_operation(
        simple_tree,
        old_text="pass",
        new_text="return 42",
        start_position=Point(0, 12)
    )
    
    editor.apply_edit(simple_tree, edit)
    assert simple_tree.root_node is not None

def test_reparse_tree(editor, python_parser, simple_tree):
    """Test reparsing tree with new source."""
    new_source = "def test(): return 42"
    new_tree = editor.reparse_tree(simple_tree, new_source, python_parser)

    assert new_tree is not None
    assert new_tree.root_node is not None
    assert new_tree.root_node.type == "module"
    assert "def test()" in new_tree.root_node.text.decode('utf8')

def test_validate_tree(editor, simple_tree):
    """Test tree validation."""
    assert editor._validate_tree(simple_tree)
    assert not editor._validate_tree(None)

def test_verify_edit_position(editor, simple_tree):
    """Test edit position verification."""
    assert editor._verify_edit_position(simple_tree.root_node, Point(0, 12), "test")
    assert not editor._verify_edit_position(None, Point(0, 0), "test")

def test_update_tree_with_edits(editor, python_parser, simple_tree):
    """Test updating tree with multiple edits."""
    edits = [
        editor.create_edit_operation(
            simple_tree,
            old_text="pass",
            new_text="return 42",
            start_position=Point(0, 12)
        )
    ]

    new_tree = editor.update_tree(simple_tree, edits, python_parser)
    assert new_tree is not None
    assert new_tree.root_node is not None
    assert new_tree.root_node.type == "module"
    assert "return 42" in new_tree.root_node.text.decode('utf8') 