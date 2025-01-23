"""Tests for tree-sitter models."""
import pytest
from tree_sitter import Node, Parser, Point
from tree_sitter_language_pack import get_binding, get_language

from src.GithubAnalyzer.analysis.models.tree_sitter import (
    get_node_text,
    node_to_dict,
    format_error_context,
    count_nodes
)

@pytest.fixture
def python_parser():
    """Create a Python parser using tree-sitter v24 API."""
    binding = get_binding('python')
    language = get_language('python')
    parser = Parser()
    parser.language = language
    return parser

@pytest.fixture
def simple_tree(python_parser):
    """Create a simple Python syntax tree."""
    code = "def hello(): pass"
    return python_parser.parse(bytes(code, "utf8"))

@pytest.fixture
def complex_tree(python_parser):
    """Create a more complex Python syntax tree."""
    code = """
def test_function(arg1, arg2):
    if arg1:
        return arg2
    else:
        return None
"""
    return python_parser.parse(bytes(code, "utf8"))

def test_get_node_text_with_content():
    """Test getting text from a node with content."""
    content = "def hello(): pass"
    # Create a mock node with start_byte and end_byte
    class MockNode:
        def __init__(self, start, end):
            self.start_byte = start
            self.end_byte = end
    
    # Test getting "hello"
    node = MockNode(4, 9)
    assert get_node_text(node, content) == "hello"
    
    # Test getting "pass"
    node = MockNode(13, 17)  # Fixed byte offsets
    assert get_node_text(node, content) == "pass"

def test_get_node_text_empty():
    """Test getting text from None node."""
    assert get_node_text(None, "any content") == ""

def test_node_to_dict_basic(simple_tree):
    """Test basic node to dictionary conversion."""
    root = simple_tree.root_node
    result = node_to_dict(root)
    
    assert result['type'] == 'module'
    assert isinstance(result['children'], list)
    assert len(result['children']) > 0
    assert result['children'][0]['type'] == 'function_definition'
    assert 'start_point' not in result
    assert 'end_point' not in result

def test_node_to_dict_with_metadata(simple_tree):
    """Test node to dictionary conversion with metadata."""
    root = simple_tree.root_node
    result = node_to_dict(root, include_metadata=True)
    
    assert result['type'] == 'module'
    assert isinstance(result['start_point'], tuple)
    assert isinstance(result['end_point'], tuple)
    assert result['start_point'] == (0, 0)
    assert result['end_point'][0] == 0  # Only check row
    assert result['end_point'][1] >= 15  # Column may vary based on whitespace

def test_format_error_context_middle():
    """Test formatting error context in middle of code."""
    code = """line 1
line 2
error here
line 4
line 5"""
    position = code.index("error")
    result = format_error_context(code, position)
    
    # Split and compare lines to ignore whitespace differences
    result_lines = [line.strip() for line in result.split('\n') if line.strip()]
    expected_lines = [
        "1 | line 1",
        "2 | line 2", 
        "3 | error here",
        "^",
        "4 | line 4",
        "5 | line 5"
    ]
    assert result_lines == [line.strip() for line in expected_lines]

def test_format_error_context_start():
    """Test formatting error context at start of code."""
    code = "error at start\nline 2\nline 3"
    position = 0
    result = format_error_context(code, position)
    
    # Split and compare lines to ignore whitespace differences
    result_lines = [line.strip() for line in result.split('\n') if line.strip()]
    expected_lines = [
        "1 | error at start",
        "^",
        "2 | line 2",
        "3 | line 3"
    ]
    assert result_lines == [line.strip() for line in expected_lines]

def test_format_error_context_end():
    """Test formatting error context at end of code."""
    code = "line 1\nline 2\nerror at end"
    position = len(code) - 1
    result = format_error_context(code, position)
    
    # Split and compare lines to ignore whitespace differences
    result_lines = [line.strip() for line in result.split('\n') if line.strip()]
    expected_lines = [
        "1 | line 1",
        "2 | line 2",
        "3 | error at end",
        "^"
    ]
    assert result_lines == [line.strip() for line in expected_lines]

def test_format_error_context_out_of_bounds():
    """Test formatting error context with position out of bounds."""
    code = "short code"
    position = len(code) + 10
    result = format_error_context(code, position)
    assert result == code

def test_format_error_context_empty():
    """Test formatting error context with empty code."""
    result = format_error_context("", 0)
    assert result == ""

def test_count_nodes_none():
    """Test counting nodes with None node."""
    assert count_nodes(None) == 0

def test_count_nodes_simple(simple_tree):
    """Test counting nodes in a simple tree."""
    count = count_nodes(simple_tree.root_node)
    # module -> function_definition -> def, identifier, parameters, pass_statement
    assert count >= 6  # At least these nodes should exist

def test_count_nodes_complex(complex_tree):
    """Test counting nodes in a complex tree."""
    count = count_nodes(complex_tree.root_node)
    # Should include module, function_definition, if_statement, return_statement, etc.
    assert count >= 10  # Complex tree should have more nodes 