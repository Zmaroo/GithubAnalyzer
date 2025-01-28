import pytest
import json
import logging
from tree_sitter import Tree, Node, Point
from tree_sitter_language_pack import get_parser, get_language

from GithubAnalyzer.services.analysis.parsers.tree_sitter_traversal import (
    TreeSitterTraversal,
    ParserError
)
from GithubAnalyzer.utils.logging.tree_sitter_logging import (
    TreeSitterLogHandler,
    StructuredFormatter
)
from GithubAnalyzer.utils.logging.logging_config import configure_logging

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
def python_parser():
    """Create a Python parser."""
    return get_parser("python")

@pytest.fixture
def simple_tree(python_parser):
    """Create a simple Python AST."""
    code = "def test(): pass"
    return python_parser.parse(bytes(code, "utf8"))

@pytest.fixture
def complex_tree(python_parser):
    """Create a more complex Python AST."""
    code = """
def hello(name):
    print(f"Hello {name}")
    return True

class Greeter:
    def __init__(self):
        pass
        
    def greet(self, name):
        print(f"Hi {name}")
"""
    return python_parser.parse(bytes(code, "utf8"))

@pytest.fixture
def traversal():
    """Create a TreeSitterTraversal instance."""
    return TreeSitterTraversal()

def test_find_nodes_by_type(complex_tree, traversal):
    """Test finding nodes by type using walk_tree()."""
    # Find all function definitions
    nodes = [
        node for node in traversal.walk_tree(complex_tree.root_node)
        if node.type == "function_definition"
    ]
    assert len(nodes) == 3  # hello, __init__, and greet
    # Verify function names
    function_names = [
        node.child_by_field_name('name').text.decode('utf8')
        for node in nodes
    ]
    assert sorted(function_names) == ['__init__', 'greet', 'hello']

def test_find_nodes_by_text(complex_tree, traversal):
    """Test finding nodes by text content."""
    # Find nodes containing specific text
    nodes = [
        node for node in traversal.walk_tree(complex_tree.root_node)
        if "hello" in node.text.decode('utf8')
    ]
    assert len(nodes) > 0
    assert any(node.type == "function_definition" for node in nodes)

def test_get_node_text(complex_tree, traversal):
    """Test getting node text."""
    # Get text from function definition
    nodes = [
        node for node in traversal.walk_tree(complex_tree.root_node)
        if node.type == "function_definition"
    ]
    assert nodes
    text = nodes[0].text.decode('utf8')
    assert "def hello" in text

def test_get_node_range(complex_tree, traversal):
    """Test getting node range using v24 properties."""
    # Get range from function definition
    nodes = [
        node for node in traversal.walk_tree(complex_tree.root_node)
        if node.type == "function_definition"
    ]
    assert nodes
    node = nodes[0]
    assert node.start_point is not None
    assert node.end_point is not None
    assert node.start_byte is not None
    assert node.end_byte is not None

def test_get_node_context(complex_tree, traversal):
    """Test getting node context using v24 features."""
    # Get context from function definition
    nodes = [
        node for node in traversal.walk_tree(complex_tree.root_node)
        if node.type == "function_definition"
    ]
    assert nodes
    node = nodes[0]
    # Get function name using child_by_field_name
    name_node = node.child_by_field_name('name')
    assert name_node is not None
    assert name_node.text.decode('utf8') == 'hello'

def test_get_named_descendants(complex_tree, caplog):
    """Test getting named descendants using named_children."""
    with caplog.at_level(logging.DEBUG, logger='tree_sitter.traversal'):
        traversal = TreeSitterTraversal()
        nodes = []
        cursor = complex_tree.walk()
        
        def collect_named_nodes(cursor):
            if cursor.node.is_named:
                nodes.append(cursor.node)
            if cursor.goto_first_child():
                collect_named_nodes(cursor)
                cursor.goto_parent()
            if cursor.goto_next_sibling():
                collect_named_nodes(cursor)
        
        collect_named_nodes(cursor)
        assert len(nodes) > 0

def test_example(simple_tree):
    traversal = TreeSitterTraversal()
    traversal._logger.info("Test log message")
    assert simple_tree.root_node is not None

def test_structured_logging(complex_tree, caplog):
    """Test structured logging output."""
    with caplog.at_level(logging.DEBUG, logger='tree_sitter.traversal'):
        traversal = TreeSitterTraversal()
        cursor = complex_tree.walk()
        nodes = []
        while cursor.goto_first_child():
            if cursor.node.is_named:
                nodes.append(cursor.node)
            cursor.goto_next_sibling()
        assert len(nodes) > 0
        assert all(isinstance(record.msg, dict) for record in caplog.records)