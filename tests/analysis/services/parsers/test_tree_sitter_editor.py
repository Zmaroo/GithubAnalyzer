"""Tests for TreeSitterEditor."""
import pytest
import json  # Add this import
from unittest.mock import patch, Mock
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
    new_code = "def test():\n    pass"
    old_tree = python_parser.parse(bytes(old_code, "utf8"))
    new_tree = python_parser.parse(bytes(new_code, "utf8"))
    changed_ranges = editor.get_changed_ranges(old_tree, new_tree)
    assert len(changed_ranges) > 0

def test_visualize_tree(editor, simple_tree, tmp_path):
    """Test visualizing a tree."""
    output_file = tmp_path / "tree.svg"
    editor.visualize_tree(simple_tree, output_file)
    assert output_file.exists()

def test_is_valid_position(editor, simple_tree):
    """Test checking if a position is valid."""
    position = Point(0, 0)
    assert editor.is_valid_position(simple_tree, position)

def test_create_edit_operation(editor, simple_tree):
    """Test creating an edit operation."""
    start = Point(0, 0)
    end = Point(0, 4)
    new_text = "def test():\n    pass"
    edit_operation = editor.create_edit_operation(simple_tree, start, end, new_text)
    assert edit_operation is not None

def test_apply_edit(editor, simple_tree):
    """Test applying an edit to a tree."""
    start = Point(0, 0)
    end = Point(0, 4)
    new_text = "def test():\n    pass"
    edit_operation = editor.create_edit_operation(simple_tree, start, end, new_text)
    editor.apply_edit(simple_tree, edit_operation)
    assert simple_tree.root_node is not None

def test_reparse_tree(editor, python_parser, simple_tree):
    """Test reparsing a tree after an edit."""
    start = Point(0, 0)
    end = Point(0, 4)
    new_text = "def test():\n    pass"
    edit_operation = editor.create_edit_operation(simple_tree, start, end, new_text)
    editor.apply_edit(simple_tree, edit_operation)
    new_tree = editor.reparse_tree(python_parser, simple_tree)
    assert new_tree.root_node is not None

def test_validate_tree(editor, simple_tree):
    """Test validating a tree."""
    assert editor.validate_tree(simple_tree)

def test_verify_edit_position(editor, simple_tree):
    """Test verifying an edit position."""
    start = Point(0, 0)
    end = Point(0, 4)
    assert editor.verify_edit_position(simple_tree, start, end)

def test_update_tree_with_edits(editor, python_parser, simple_tree):
    """Test updating a tree with multiple edits."""
    edits = [
        editor.create_edit_operation(simple_tree, Point(0, 0), Point(0, 4), "def test():\n    pass"),
        editor.create_edit_operation(simple_tree, Point(1, 0), Point(1, 4), "print('Hello')")
    ]
    new_tree = editor.update_tree_with_edits(python_parser, simple_tree, edits)
    assert new_tree.root_node is not None