"""Tests for TreeSitterTraversal."""
import pytest
import logging
import logging.config
from tree_sitter import Tree, Node, Point
from tree_sitter_language_pack import get_parser
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_traversal import TreeSitterTraversal
from src.GithubAnalyzer.core.utils.logging import get_logging_config
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_logging import TreeSitterLogHandler

@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Configure logging for tests."""
    # Get logging config
    config = get_logging_config()
    
    # Update config for testing
    config['loggers']['tree_sitter.traversal'] = {
        'handlers': ['default'],
        'level': 'DEBUG',
        'propagate': True
    }
    
    # Configure default handler for debug level
    config['handlers']['default']['level'] = 'DEBUG'
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Set caplog level
    caplog.set_level(logging.DEBUG, logger='tree_sitter.traversal')
    
    # Create logger instance
    logger = logging.getLogger('tree_sitter.traversal')
    
    # Create and add tree-sitter handler
    handler = TreeSitterLogHandler(logger)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))
    logger.addHandler(handler)
    
    return logger

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

def test_find_nodes_by_type(complex_tree):
    """Test finding nodes by type."""
    # Find all function definitions
    nodes = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")
    assert len(nodes) == 3  # hello, __init__, and greet
    
    # Find all string literals
    strings = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "string")
    assert len(strings) > 0

def test_find_nodes_by_text(complex_tree):
    """Test finding nodes by text content."""
    # Find nodes containing specific text
    nodes = TreeSitterTraversal.find_nodes_by_text(complex_tree.root_node, "hello")
    assert len(nodes) > 0
    assert any(node.type == "function_definition" for node in nodes)

def test_get_node_text(complex_tree):
    """Test getting node text."""
    # Get text from function definition
    func_nodes = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")
    assert len(func_nodes) > 0
    
    text = TreeSitterTraversal.get_node_text(func_nodes[0])
    assert text is not None
    assert "def hello" in text

def test_get_node_range(complex_tree):
    """Test getting node range."""
    # Get range from function definition
    func_nodes = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")
    assert len(func_nodes) > 0
    
    range_info = TreeSitterTraversal.get_node_range(func_nodes[0])
    assert isinstance(range_info, dict)
    assert "start_point" in range_info
    assert "end_point" in range_info
    assert "start_byte" in range_info
    assert "end_byte" in range_info

def test_get_node_context(complex_tree):
    """Test getting node context."""
    # Get context from function definition
    func_nodes = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")
    assert len(func_nodes) > 0
    
    context = TreeSitterTraversal.get_node_context(func_nodes[0])
    assert context is not None
    assert "node" in context
    assert "text" in context
    assert "range" in context

def test_get_named_descendants(complex_tree, caplog):
    """Test getting named descendants."""
    # Set up logging capture
    with caplog.at_level(logging.DEBUG, logger='tree_sitter.traversal'):
        # Get named descendants from root node
        traversal = TreeSitterTraversal()
        descendants = traversal.get_named_descendants(
            node=complex_tree.root_node,
            start_byte=0,
            end_byte=complex_tree.root_node.end_byte
        )

        # Print captured logs for debugging
        print("\nCaptured logs:")
        for record in caplog.records:
            print(f"{record.levelname} - {record.name} - {record.getMessage()}")

        # Verify logging output
        assert any("Getting named descendants" in record.getMessage() for record in caplog.records), "Debug log message not found"
        assert len(descendants) > 0, "No descendants found"

def test_get_node_by_position(complex_tree):
    """Test getting node at position."""
    # Get node at specific position
    node = TreeSitterTraversal.find_node_at_position(complex_tree.root_node, Point(1, 4))
    assert node is not None
    assert isinstance(node, Node)

def test_get_node_path(complex_tree):
    """Test getting node path."""
    # Get path to a nested node
    func_nodes = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")
    assert len(func_nodes) > 0
    
    path = TreeSitterTraversal.get_node_path(func_nodes[0])
    assert len(path) > 0
    assert path[0] == complex_tree.root_node
    assert path[-1] == func_nodes[0]

def test_get_common_ancestor(complex_tree):
    """Test getting common ancestor."""
    # Get common ancestor of two nodes
    nodes = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")
    assert len(nodes) >= 2
    
    ancestor = TreeSitterTraversal.find_common_ancestor(nodes[0], nodes[1])
    assert ancestor is not None
    assert isinstance(ancestor, Node)

def test_get_node_depth(complex_tree):
    """Test getting node depth."""
    # Get depth of various nodes
    nodes = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")
    assert len(nodes) > 0
    
    for node in nodes:
        depth = TreeSitterTraversal.get_node_depth(node)
        assert depth >= 0
        # Class methods should be deeper than top-level functions
        if "greet" in TreeSitterTraversal.get_node_text(node):
            assert depth > 1 