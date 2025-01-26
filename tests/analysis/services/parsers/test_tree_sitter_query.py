import pytest
import json
import logging
from tree_sitter import Tree, Node, Point, Query, QueryError
from tree_sitter_language_pack import get_parser, get_language

from GithubAnalyzer.services.analysis.parsers.tree_sitter_query import (
    TreeSitterQueryHandler,
    QueryError,
    QueryOptimizationSettings
)
from GithubAnalyzer.utils.logging.tree_sitter_logging import (
    TreeSitterLogHandler,
    StructuredFormatter
)
from GithubAnalyzer.utils.logging.logging_config import configure_logging

from GithubAnalyzer.services.analysis.parsers.tree_sitter_traversal import TreeSitterTraversal
"""Tests for TreeSitterQueryHandler."""

@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for all tests."""
    configure_logging(level=logging.DEBUG, structured=True, enable_tree_sitter=True)
    root_logger = logging.getLogger('tree_sitter')
    if not any(isinstance(h, TreeSitterLogHandler) for h in root_logger.handlers):
        handler = TreeSitterLogHandler()
        handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(handler)
    yield
    # Clean up handlers after test
    root_logger.handlers.clear()

@pytest.fixture
def query_handler():
    """Create a TreeSitterQueryHandler instance."""
    logger = TreeSitterLogHandler('tree_sitter.query')
    return TreeSitterQueryHandler(logger)

@pytest.fixture
def python_parser():
    return get_parser("python")

@pytest.fixture
def python_tree(python_parser):
    code = "def test(): pass"
    return python_parser.parse(bytes(code, "utf8"))

@pytest.fixture
def python_tree_with_all_patterns(python_parser):
    """Create a Python tree containing all pattern types for testing."""
    code = """
from sys import path

def standalone_function():
    return 42

class TestClass:
    \"\"\"Class docstring.\"\"\"
    def method(self):
        self.attribute = "test"
        print("Hello")  # Comment
        os.path.join("a", "b")
"""
    return python_parser.parse(bytes(code, "utf8"))

@pytest.fixture
def python_query():
    """Sample Python query for testing."""
    return """
    (function_definition) @function
    """

def test_create_query(query_handler):
    """Test creating a query."""
    language = get_language("python")
    query = Query(language, "(function_definition) @function")
    assert query is not None

def test_create_query_errors(query_handler):
    """Test creating a query with errors."""
    language = get_language("python")
    with pytest.raises(QueryError):
        Query(language, "(invalid_syntax) @error")

def test_execute_query(query_handler, python_tree):
    """Test executing a query."""
    language = get_language("python")
    query = Query(language, "(function_definition) @function")
    matches = query.matches(python_tree.root_node)
    assert len(matches) > 0

def test_get_matches(query_handler, python_tree):
    """Test getting matches from a query."""
    language = get_language("python")
    query = Query(language, "(function_definition) @function")
    matches = query.matches(python_tree.root_node)
    assert len(matches) > 0

def test_find_nodes(query_handler, python_parser):
    """Test finding nodes in a tree."""
    code = "def test(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    cursor = tree.walk()
    nodes = []
    while cursor.goto_first_child():
        if cursor.node.type == "function_definition":
            nodes.append(cursor.node)
        cursor.goto_next_sibling()
    assert len(nodes) > 0

def test_find_nodes_with_unicode(query_handler, python_parser):
    """Test finding nodes with unicode characters."""
    code = "def test(): pass\nprint('こんにちは')"
    tree = python_parser.parse(bytes(code, "utf8"))
    cursor = tree.walk()
    nodes = []
    while cursor.goto_first_child():
        if cursor.node.type == "function_definition":
            nodes.append(cursor.node)
        cursor.goto_next_sibling()
    assert len(nodes) > 0

def test_find_nodes_with_all_patterns(query_handler, python_parser):
    """Test finding nodes with all available pattern types."""
    source = """
# This is a comment
def test_class():
    x = "string"
    obj.attr = 42
    func()
    return x

class MyClass:
    pass
"""
    tree = python_parser.parse(bytes(source, "utf8"))
    cursor = tree.walk()
    
    # Test finding different node types
    node_types = {
        "function_definition": 0,
        "class_definition": 0,
        "string": 0,
        "comment": 0,
        "call": 0,
        "attribute": 0
    }
    
    def count_node_types(cursor):
        if cursor.node.type in node_types:
            node_types[cursor.node.type] += 1
        if cursor.goto_first_child():
            count_node_types(cursor)
            cursor.goto_parent()
        if cursor.goto_next_sibling():
            count_node_types(cursor)
    
    count_node_types(cursor)
    assert sum(node_types.values()) > 0

def test_structured_logging(complex_tree, caplog):
    """Test structured logging output."""
    with caplog.at_level(logging.DEBUG, logger='tree_sitter.query'):
        cursor = complex_tree.walk()
        nodes = []
        while cursor.goto_first_child():
            if cursor.node.is_named:
                nodes.append(cursor.node)
            cursor.goto_next_sibling()
        assert len(nodes) > 0
        assert all(isinstance(record.msg, dict) for record in caplog.records)