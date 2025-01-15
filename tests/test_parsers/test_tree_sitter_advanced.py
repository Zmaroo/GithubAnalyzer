"""Advanced tests for the TreeSitterParser."""

from pathlib import Path
from typing import Dict, List, Generator

import pytest
from tree_sitter import Node, Tree, TreeCursor

from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.models.analysis.ast import ParseResult
from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser


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
    assert result.is_valid
    assert result.metadata["encoding"] == "utf8"

    # Test UTF-8 with Unicode
    content_unicode = 'print("Hello, 世界! 🌍")'
    result = parser.parse(content_unicode, "python")
    assert result.is_valid
    assert result.metadata["encoding"] == "utf8"


def test_node_traversal(parser: TreeSitterParser) -> None:
    """Test node traversal functionality."""
    content = """
def test_function():
    x = 1
    y = 2
    return x + y
"""
    result = parser.parse(content, "python")
    assert result.is_valid

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
    assert result.is_valid

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
        print(f"\nTesting code:\n{code}")
        print(f"Tree root type: {result.ast.root_node.type}")
        print(f"Tree has error: {result.ast.root_node.has_error}")
        print(f"Tree errors: {result.errors}")

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


def test_query_functionality(parser: TreeSitterParser) -> None:
    """Test query functionality."""
    content = """
def test_function():
    x = 1
    y = 2
    print(x + y)
    return x + y

def another_function():
    print("Hello")
"""
    result = parser.parse(content, "python")
    assert result.is_valid

    # Get all function definitions using the parser's query functionality
    functions = result.metadata["analysis"]["functions"]
    assert len(functions) == 2
    assert "test_function" in functions
    assert "another_function" in functions


def test_error_recovery(parser: TreeSitterParser) -> None:
    """Test parser error recovery capabilities."""
    content = """
def valid_function():
    return 42

def invalid_function)
    print("Hello")

def another_valid():
    pass
"""
    result = parser.parse(content, "python")

    # Even with errors, we should get a parse tree
    assert result.ast is not None

    # The error should be detected
    assert not result.is_valid
    assert len(result.errors) > 0

    # Debug: Print AST structure
    def print_node(node, level=0):
        indent = "  " * level
        print(f"{indent}{node.type}: {node.text.decode('utf8')}")
        for child in node.children:
            print_node(child, level + 1)

    print("\nAST Structure:")
    print_node(result.ast.root_node)

    # We should still be able to find valid functions
    valid_functions = result.metadata["analysis"]["functions"]

    assert "valid_function" in valid_functions
    assert "another_valid" in valid_functions


def test_metadata_completeness(parser: TreeSitterParser) -> None:
    """Test completeness of parse result metadata."""
    content = "x = 42"
    result = parser.parse(content, "python")

    assert result.metadata["encoding"] == parser._encoding
    assert result.metadata["raw_content"] == content
    assert result.metadata["root_type"] == "module"
    assert "analysis" in result.metadata
    assert isinstance(result.metadata["analysis"], dict)
    assert "errors" in result.metadata["analysis"]
