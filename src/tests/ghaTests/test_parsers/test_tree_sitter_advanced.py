"""Advanced tests for the TreeSitterParser."""

from pathlib import Path
from typing import Dict, List, Generator

import pytest
from tree_sitter import Node, Tree, TreeCursor

from GithubAnalyzer.core.models.errors import ParserError
from GithubAnalyzer.analysis.models.tree_sitter import TreeSitterResult
from GithubAnalyzer.analysis.services.parsers.tree_sitter import TreeSitterParser
from GithubAnalyzer.analysis.models.tree_sitter import TreeSitterEdit, TreeSitterRange


@pytest.fixture
def parser() -> Generator[TreeSitterParser, None, None]:
    """Create a TreeSitterParser instance."""
    parser = TreeSitterParser()
    parser.initialize(["python"])  # Initialize only Python for faster tests
    yield parser
    parser.cleanup()


def test_encoding_handling(parser: TreeSitterParser) -> None:
    """Test handling of text encodings."""
    # Test UTF-8 with ASCII
    content_ascii = 'print("Hello!")'
    result = parser.parse(content_ascii, "python")
    assert result.success
    assert "byte_length" in result.metadata

    # Test UTF-8 with Unicode
    content_unicode = 'print("Hello, 世界! 🌍")'
    result = parser.parse(content_unicode, "python")
    assert result.success
    assert "byte_length" in result.metadata


def test_node_traversal(parser: TreeSitterParser) -> None:
    """Test node traversal functionality."""
    content = """
def test_function():
    x = 1
    y = 2
    return x + y
"""
    result = parser.parse(content, "python")
    assert result.success

    # Get root node
    root: Node = result.ast.root_node
    assert root.type == "module"

    # Check function definition
    func_def = root.children[0]
    assert func_def.type == "function_definition"

    # Check function name
    func_name = func_def.child_by_field_name("name")
    assert func_name.text.decode("utf8") == "test_function"

    # Check function body
    body = func_def.child_by_field_name("body")
    assert body.type == "block"
    assert len(body.children) > 0


def test_cursor_operations(parser: TreeSitterParser) -> None:
    """Test tree cursor operations."""
    content = """
def example():
    if True:
        return 42
"""
    result = parser.parse(content, "python")
    assert result.success

    cursor: TreeCursor = result.ast.walk()

    # Start at module
    assert cursor.node.type == "module"

    # Go to function definition
    assert cursor.goto_first_child()
    assert cursor.node.type == "function_definition"

    # Go to function name
    assert cursor.goto_first_child()
    assert cursor.node.type == "def"

    # Go to next sibling (identifier)
    assert cursor.goto_next_sibling()
    assert cursor.node.type == "identifier"
    assert cursor.node.text.decode("utf8") == "example"


def test_syntax_error_detection(parser: TreeSitterParser) -> None:
    """Test detection of syntax errors."""
    test_cases = [
        (
            # Missing parenthesis
            """
def test:
    print("Hello")
""",
            "ERROR",
        ),
        (
            # Invalid indentation - Tree-sitter doesn't consider this an error
            """
def test():
print("Hello")
""",
            None,  # Not an error according to Tree-sitter
        ),
        (
            # Unclosed string
            """
print("Hello)
""",
            "ERROR",
        ),
    ]

    for code, expected_error in test_cases:
        result = parser.parse(code, "python")
        if expected_error == "ERROR":
            assert not result.is_valid
            assert len(result.errors) > 0
        else:
            assert result.is_valid
            assert len(result.errors) == 0


def test_node_counting(parser: TreeSitterParser) -> None:
    """Test node counting functionality."""
    test_cases = [
        ("x = 1", 3),  # assignment, identifier, number
        ("def f(): pass", 4),  # function_definition, identifier, parameters, pass
        ("if True: pass", 4),  # if, True, block, pass
        ("x = 1 + 2", 5),  # assignment, identifier, binary_operator, number, number
    ]

    for code, expected_count in test_cases:
        result = parser.parse(code, "python")
        assert result.is_valid
        assert result.node_count >= expected_count


def test_error_recovery(parser: TreeSitterParser) -> None:
    """Test parser error recovery capabilities."""
    content = """def valid_function():
    return 42

def invalid_function)
    print("Hello")

def another_valid():
    pass"""
    
    # Ensure consistent line endings and no leading whitespace
    normalized_content = "\n".join(line.strip() for line in content.splitlines())
    result = parser.parse(normalized_content, "python")

    # Even with errors, we should get a parse tree
    assert result.ast is not None

    # The error should be detected
    assert not result.is_valid
    assert len(result.errors) > 0

    # We should still be able to find valid nodes
    root = result.ast.root_node
    valid_functions = [
        node.child_by_field_name("name").text.decode("utf8")
        for node in root.children
        if node.type == "function_definition" and not node.has_error
    ]

    assert "valid_function" in valid_functions
    assert "another_valid" in valid_functions


def test_metadata_completeness(parser: TreeSitterParser) -> None:
    """Test completeness of parse result metadata."""
    content = "x = 42"
    result = parser.parse(content, "python")

    assert "byte_length" in result.metadata
    assert "line_count" in result.metadata
    assert "root_type" in result.metadata
    assert result.metadata["root_type"] == "module"
    assert isinstance(result.metadata, dict)


def test_incremental_parsing(parser: TreeSitterParser) -> None:
    """Test incremental parsing functionality."""
    # Initial content
    content = """
def example():
    x = 1
    y = 2
    return x + y
"""
    result = parser.parse(content, "python")
    assert result.success
    tree = result.ast

    # Modified content
    modified_content = """
def example():
    x = 42
    y = 2
    return x + y
"""
    # Find the position of "1" in the original content
    lines = content.splitlines()
    line_with_x = next(i for i, line in enumerate(lines) if "x = 1" in line)
    column_of_1 = lines[line_with_x].index("1")
    
    # Calculate byte offset
    start_byte = sum(len(line) + 1 for line in lines[:line_with_x]) + column_of_1
    end_byte = start_byte + 1  # "1" is one byte long
    
    # Find the node at this position
    node = tree.root_node.descendant_for_byte_range(start_byte, end_byte)
    assert node is not None, "Failed to find node to edit"
    assert node.text.decode("utf8") == "1"
    print(f"Found node at edit position: type={node.type}, text={node.text.decode('utf8')}")
    print(f"Node position: start_byte={node.start_byte}, end_byte={node.end_byte}")
    print(f"Node point: start={node.start_point}, end={node.end_point}")

    # Parse the modified content first
    result = parser.parse(modified_content, "python")
    assert result.success
    new_tree = result.ast

    # Find the position of "42" in the modified content
    lines = modified_content.splitlines()
    line_with_x = next(i for i, line in enumerate(lines) if "x = 42" in line)
    column_of_42 = lines[line_with_x].index("42")
    
    # Calculate byte offset in modified content
    new_start_byte = sum(len(line) + 1 for line in lines[:line_with_x]) + column_of_42
    new_end_byte = new_start_byte + len("42")

    # Edit the original tree to match the new content
    tree.edit(
        start_byte=node.start_byte,
        old_end_byte=node.end_byte,
        new_end_byte=node.start_byte + len("42"),
        start_point=node.start_point,
        old_end_point=node.end_point,
        new_end_point=(node.start_point[0], node.start_point[1] + len("42"))
    )

    # Parse the modified content with the edited tree
    result = parser.parse(modified_content, "python", old_tree=tree)
    assert result.success

    # Verify the new tree has the correct value
    new_node = result.ast.root_node.descendant_for_byte_range(new_start_byte, new_end_byte)
    assert new_node is not None, "Could not find node in new tree"
    assert new_node.text.decode("utf8") == "42"
