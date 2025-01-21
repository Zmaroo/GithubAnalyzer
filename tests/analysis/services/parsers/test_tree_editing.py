"""Tests for Tree-sitter tree editing functionality."""

import pytest
import logging
from tree_sitter import Node, Tree, Parser, Language

from src.GithubAnalyzer.analysis.services.parsers.tree_sitter import TreeSitterParser, tree_sitter_logger

@pytest.fixture
def parser():
    """Create parser instance for testing."""
    parser = TreeSitterParser()
    # Set logger directly as documented in v24
    for lang_parser in parser.parsers.values():
        # Don't set logger for now as it's causing issues with Python 3.13
        lang_parser.timeout_micros = 5000 * 1000  # 5 seconds in microseconds
    return parser

def test_edit_missing_colon(parser):
    """Test adding missing colon through tree edit."""
    code = """
    def test()  # Missing colon
        print("Hello")
    """.encode('utf8')  # Convert to bytes as required
    
    # Initial parse
    result = parser.parse(code, "python")
    assert not result.is_valid
    
    # Store reference to tree before editing
    tree = result.tree
    
    # Use proper cursor methods as documented
    cursor = tree.walk()
    error_node = None
    
    # Navigate tree as documented
    if cursor.goto_first_child():
        while True:
            if cursor.node.type == "ERROR":
                error_node = cursor.node
                break
            if not cursor.goto_next_sibling():
                break
            
    assert error_node is not None
    assert error_node.has_error
    
    # Create edit
    edit = parser.create_edit_for_missing_colon(error_node)
    
    # Keep original tree for comparison
    original_tree = tree.copy()
    
    # Apply edit directly to tree as documented
    tree.edit(
        start_byte=edit['start_byte'],
        old_end_byte=edit['old_end_byte'],
        new_end_byte=edit['new_end_byte'],
        start_point=edit['start_point'],
        old_end_point=edit['old_end_point'],
        new_end_point=edit['new_end_point']
    )
    
    # Re-parse with edited tree as old_tree and updated source
    edited_code = code[:edit['start_byte']] + b':' + code[edit['old_end_byte']:]
    edited_result = parser.parse(edited_code, "python", old_tree=tree)
    
    # Keep reference to new tree
    new_tree = edited_result.tree
    
    # Verify edit using tree-sitter's changed_ranges
    changes = original_tree.changed_ranges(new_tree)
    assert len(changes) == 1
    assert changes[0].start_byte == edit['start_byte']
    assert changes[0].end_byte == edit['new_end_byte']

def test_batch_edit_validation(parser):
    """Test batch edit validation and ordering."""
    code = b"def test(x):"  # Use bytes directly
    result = parser.parse(code, "python")
    original_tree = result.tree.copy()
    
    edits = [
        {
            'start_byte': 10,
            'old_end_byte': 10,
            'new_end_byte': 11,
            'start_point': (0, 10),
            'old_end_point': (0, 10),
            'new_end_point': (0, 11),
            'text': b':'
        },
        {
            'start_byte': 5,
            'old_end_byte': 5,
            'new_end_byte': 6,
            'start_point': (0, 5),
            'old_end_point': (0, 5),
            'new_end_point': (0, 6),
            'text': b'('
        }
    ]
    
    # Should sort by position
    sorted_edits = parser.create_batch_edit(edits)
    edited_tree = parser.edit_tree(result.tree, sorted_edits)
    
    # Verify edits using tree-sitter's changed_ranges
    changes = original_tree.changed_ranges(edited_tree)
    assert len(changes) == 2
    assert changes[0].start_byte == sorted_edits[0]['start_byte']
    assert changes[1].start_byte == sorted_edits[1]['start_byte']

def test_overlapping_edits(parser):
    """Test detection of overlapping edits."""
    code = b"def test:"  # Use bytes directly
    result = parser.parse(code, "python")
    
    overlapping_edits = [
        {
            'start_byte': 5,
            'old_end_byte': 5,
            'new_end_byte': 7,
            'start_point': (0, 5),
            'old_end_point': (0, 5),
            'new_end_point': (0, 7),
            'text': b'()'
        },
        {
            'start_byte': 6,
            'old_end_byte': 6,
            'new_end_byte': 7,
            'start_point': (0, 6),
            'old_end_point': (0, 6),
            'new_end_point': (0, 7),
            'text': b':'
        }
    ]
    
    with pytest.raises(ValueError, match="Overlapping edits"):
        parser.create_batch_edit(overlapping_edits)

def test_indentation_edit(parser):
    """Test creating indentation edits."""
    code = b"""
    def test():
    print("Hello")  # Wrong indentation
    """  # Use bytes directly
    result = parser.parse(code, "python")
    original_tree = result.tree.copy()
    
    # Find print statement node using tree cursor
    cursor = result.tree.walk()
    print_node = None
    while cursor.goto_first_child():
        if cursor.node.type == "print_statement":
            print_node = cursor.node
            break
            
    assert print_node is not None
    
    # Create indent edit
    edit = parser.create_edit_for_indent(print_node, indent_level=4)
    assert edit is not None
    edited_tree = parser.edit_tree(result.tree, [edit])
    
    # Verify edit using tree-sitter's changed_ranges
    changes = original_tree.changed_ranges(edited_tree)
    assert len(changes) == 1
    assert changes[0].end_byte - changes[0].start_byte == len(edit['text'])
    assert edit['text'] == b'    '  # 4 spaces 