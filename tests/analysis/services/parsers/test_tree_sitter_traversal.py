"""Tests for tree-sitter traversal utilities."""
import pytest
from tree_sitter import Point, Range, Parser
from tree_sitter_language_pack import get_binding, get_language
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_traversal import TreeSitterTraversal

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
def hello(name):
    print(f"Hello {name}")
    
class Test:
    def method(self):
        pass
"""
    return python_parser.parse(bytes(code, "utf8"))

def test_walk_tree_simple(simple_tree):
    """Test walking a simple tree."""
    nodes = list(TreeSitterTraversal.walk_tree(simple_tree.root_node))
    # The tree should contain at least: module, function_definition, identifier, parameters, pass_statement
    assert len(nodes) >= 5
    assert nodes[0].type == "module"
    assert any(node.type == "function_definition" for node in nodes)
    assert any(node.type == "identifier" and node.text.decode('utf8') == "hello" for node in nodes)
    assert any(node.type == "parameters" for node in nodes)
    assert any(node.type == "pass_statement" for node in nodes)

def test_walk_tree_complex(complex_tree):
    """Test walking a complex tree."""
    nodes = list(TreeSitterTraversal.walk_tree(complex_tree.root_node))
    # The tree should contain: module, function_definition, class_definition, method_definition
    assert len(nodes) > 10  # Complex tree should have more nodes
    assert nodes[0].type == "module"
    assert len([node for node in nodes if node.type == "function_definition"]) == 2  # hello and method
    assert any(node.type == "class_definition" for node in nodes)
    assert any(node.type == "identifier" and node.text.decode('utf8') == "Test" for node in nodes)
    assert any(node.type == "string_content" and node.text.decode('utf8') == "Hello " for node in nodes)

def test_walk_tree_empty(python_parser):
    """Test walking an empty tree."""
    tree = python_parser.parse(bytes("", "utf8"))
    nodes = list(TreeSitterTraversal.walk_tree(tree.root_node))
    assert len(nodes) == 1  # Should only contain the module node
    assert nodes[0].type == "module"

def test_walk_tree_single_node(python_parser):
    """Test walking a tree with a single statement."""
    tree = python_parser.parse(bytes("pass", "utf8"))
    nodes = list(TreeSitterTraversal.walk_tree(tree.root_node))
    assert len(nodes) == 3  # Should contain module, pass_statement, and "pass" token
    assert nodes[0].type == "module"
    assert nodes[1].type == "pass_statement"
    assert nodes[2].type == "pass"

def test_find_nodes_by_type(complex_tree):
    """Test finding nodes by type."""
    # Find all function definitions
    functions = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")
    assert len(functions) == 2  # hello and method
    
    # Find all identifiers
    identifiers = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "identifier")
    assert len(identifiers) >= 3  # hello, Test, method
    assert any(node.text.decode('utf8') == "hello" for node in identifiers)
    assert any(node.text.decode('utf8') == "Test" for node in identifiers)
    assert any(node.text.decode('utf8') == "method" for node in identifiers)

def test_find_parent_of_type(complex_tree):
    """Test finding parent node by type."""
    # Find a pass_statement node
    pass_nodes = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "pass_statement")
    pass_node = pass_nodes[0]
    
    # Create traversal instance for instance method
    traversal = TreeSitterTraversal()
    
    # Find its parent function
    function = traversal.find_parent_of_type(pass_node, "function_definition")
    assert function is not None
    assert function.type == "function_definition"
    
    # Find its parent class
    class_node = traversal.find_parent_of_type(pass_node, "class_definition")
    assert class_node is not None
    assert class_node.type == "class_definition"
    
    # Try to find non-existent parent type
    non_existent = traversal.find_parent_of_type(pass_node, "non_existent")
    assert non_existent is None

def test_find_node_at_position(complex_tree):
    """Test finding node at position."""
    # Find the 'hello' function name
    node = TreeSitterTraversal.find_node_at_position(complex_tree, Point(1, 4))  # Line 1, column 4
    assert node is not None
    assert node.type == "identifier"
    assert node.text.decode('utf8') == "hello"
    
    # Find node at invalid position - should return None or the root node
    node = TreeSitterTraversal.find_node_at_position(complex_tree, Point(100, 0))
    assert node is None or node.type == "module"  # Either None or root node is acceptable

def test_get_node_context(complex_tree):
    """Test getting node context."""
    # Find the 'method' function
    method_nodes = [n for n in TreeSitterTraversal.walk_tree(complex_tree.root_node) 
                   if n.type == "function_definition" and 
                   any(c.type == "identifier" and c.text.decode('utf8') == "method" 
                       for c in TreeSitterTraversal.walk_tree(n))]
    method_node = method_nodes[0]
    
    # Get context with default lines
    context = TreeSitterTraversal.get_node_context(method_node)
    assert context['node'] == method_node
    assert context['start_line'] >= 0
    assert context['end_line'] > context['start_line']
    assert context['context_before'] == 2
    assert context['context_after'] == 2
    
    # Get context with custom lines
    context = TreeSitterTraversal.get_node_context(method_node, context_lines=1)
    assert context['context_before'] == 1
    assert context['context_after'] == 1

def test_find_child_by_field(complex_tree):
    """Test finding child by field name."""
    # Find a function definition
    functions = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")
    function = functions[0]  # 'hello' function
    
    # Find its name field
    name_node = TreeSitterTraversal.find_child_by_field(function, "name")
    assert name_node is not None
    assert name_node.type == "identifier"
    assert name_node.text.decode('utf8') == "hello"
    
    # Try to find non-existent field
    non_existent = TreeSitterTraversal.find_child_by_field(function, "non_existent")
    assert non_existent is None

def test_get_named_descendants(complex_tree):
    """Test getting named descendants in a byte range."""
    # Get the byte range of the hello function
    hello_func = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")[0]
    descendants = TreeSitterTraversal.get_named_descendants(complex_tree.root_node, hello_func.start_byte, hello_func.end_byte)
    assert descendants is not None
    assert descendants.type == "function_definition"

def test_create_cursor_at_point(complex_tree):
    """Test creating cursor at a point."""
    # Create cursor at the start of 'hello' function
    cursor = TreeSitterTraversal.create_cursor_at_point(complex_tree.root_node, (1, 4))  # Point to 'hello'
    assert cursor is not None
    
    # Create cursor at invalid point
    cursor = TreeSitterTraversal.create_cursor_at_point(complex_tree.root_node, (100, 0))
    assert cursor is None

def test_walk_descendants(complex_tree):
    """Test walking descendants."""
    # Get the hello function node
    hello_func = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")[0]
    
    # Walk its descendants
    descendants = list(TreeSitterTraversal.walk_descendants(hello_func))
    assert len(descendants) > 0
    assert any(node.type == "identifier" and node.text.decode('utf8') == "hello" for node in descendants)
    assert any(node.type == "parameters" for node in descendants)

def test_walk_named_descendants(complex_tree):
    """Test walking named descendants."""
    # Get the hello function node
    hello_func = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")[0]
    
    # Walk its named descendants
    descendants = list(TreeSitterTraversal.walk_named_descendants(hello_func))
    assert len(descendants) > 0
    assert all(node.is_named for node in descendants)
    assert any(node.type == "identifier" and node.text.decode('utf8') == "hello" for node in descendants)

def test_find_node_at_point(complex_tree):
    """Test finding node at point."""
    # Find node at the start of 'hello' function
    node = TreeSitterTraversal.find_node_at_point(complex_tree.root_node, Point(1, 4))
    assert node is not None
    assert node.type == "identifier"
    assert node.text.decode('utf8') == "hello"
    
    # Find node at invalid point - should return None or the root node
    node = TreeSitterTraversal.find_node_at_point(complex_tree.root_node, Point(100, 0))
    assert node is None or node.type == "module"  # Either None or root node is acceptable

def test_find_nodes_in_range(complex_tree):
    """Test finding nodes in range."""
    # Find nodes in the range of the hello function
    hello_func = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")[0]
    start_point = Point(*hello_func.start_point)
    end_point = Point(*hello_func.end_point)
    range_obj = Range(start_point=start_point, end_point=end_point, 
                     start_byte=hello_func.start_byte, end_byte=hello_func.end_byte)
    
    nodes = TreeSitterTraversal.find_nodes_in_range(complex_tree.root_node, range_obj)
    assert len(nodes) > 0  # Should find at least the function node itself

def test_get_next_node(complex_tree):
    """Test getting next node in traversal order."""
    # Get the hello function node
    hello_func = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")[0]
    
    # Get next node (should be 'def' keyword)
    next_node = TreeSitterTraversal.get_next_node(hello_func)
    assert next_node is not None
    assert next_node.type == "def"  # First child is the 'def' keyword
    
    # Get next node after 'def' (should be identifier 'hello')
    next_node = TreeSitterTraversal.get_next_node(next_node)
    assert next_node is not None
    assert next_node.type == "identifier"
    assert next_node.text.decode('utf8') == "hello"

def test_get_node_path(complex_tree):
    """Test getting path from root to node."""
    # Find the pass statement inside the method
    pass_nodes = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "pass_statement")
    pass_node = pass_nodes[0]
    
    # Get path from root to pass statement
    path = TreeSitterTraversal.get_node_path(pass_node)
    
    # Verify path
    assert len(path) >= 5  # module -> class -> function -> block -> pass
    assert path[0].type == "module"  # Root should be module
    assert path[-1] == pass_node  # Last node should be our pass statement
    assert any(node.type == "class_definition" for node in path)
    assert any(node.type == "function_definition" for node in path)
    assert any(node.type == "block" for node in path) 

def test_find_common_ancestor(complex_tree):
    """Test finding common ancestor of two nodes."""
    # Find the 'hello' and 'method' functions
    functions = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")
    hello_func = functions[0]
    method_func = functions[1]
    
    # Their common ancestor should be the module node
    common = TreeSitterTraversal.find_common_ancestor(hello_func, method_func)
    assert common is not None
    assert common.type == "module"
    
    # Find common ancestor of method and its pass statement
    pass_nodes = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "pass_statement")
    pass_node = pass_nodes[0]
    
    common = TreeSitterTraversal.find_common_ancestor(method_func, pass_node)
    assert common is not None
    assert common.type == "function_definition"  # The method function should be their common ancestor

def test_get_node_range(complex_tree):
    """Test getting node range."""
    # Get range of hello function
    hello_func = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "function_definition")[0]
    range_obj = TreeSitterTraversal.get_node_range(hello_func)
    
    # Verify range properties
    assert range_obj.start_point == hello_func.start_point
    assert range_obj.end_point == hello_func.end_point
    assert range_obj.start_byte == hello_func.start_byte
    assert range_obj.end_byte == hello_func.end_byte

def test_traverse_tree(complex_tree):
    """Test traversing tree nodes."""
    # Create traversal instance
    traversal = TreeSitterTraversal()
    
    # Get all nodes
    nodes = list(traversal.traverse_tree(complex_tree.root_node))
    
    # Verify basic properties
    assert len(nodes) > 0
    assert nodes[0] == complex_tree.root_node
    assert any(node.type == "function_definition" for node in nodes)
    assert any(node.type == "class_definition" for node in nodes)
    assert any(node.type == "identifier" and node.text.decode('utf8') == "hello" for node in nodes)
    assert any(node.type == "identifier" and node.text.decode('utf8') == "Test" for node in nodes)

def test_instance_find_parent_of_type(complex_tree):
    """Test instance method for finding parent of type."""
    # Create traversal instance
    traversal = TreeSitterTraversal()
    
    # Find pass statement and its parent function
    pass_nodes = TreeSitterTraversal.find_nodes_by_type(complex_tree.root_node, "pass_statement")
    pass_node = pass_nodes[0]
    
    # Find parent function using instance method
    function = traversal.find_parent_of_type(pass_node, "function_definition")
    assert function is not None
    assert function.type == "function_definition"
    
    # Find parent class
    class_node = traversal.find_parent_of_type(pass_node, "class_definition")
    assert class_node is not None
    assert class_node.type == "class_definition"
    
    # Try to find non-existent parent type
    non_existent = traversal.find_parent_of_type(pass_node, "non_existent")
    assert non_existent is None 

def test_find_node_at_position_logs_error(complex_tree, caplog):
    """Test that find_node_at_position logs errors."""
    # Cause an error by passing None
    TreeSitterTraversal.find_node_at_position(None, Point(0, 0))
    assert "Error finding node at position" in caplog.text

def test_find_child_by_field_logs_error(complex_tree, caplog):
    """Test that find_child_by_field logs errors."""
    # Cause an error by passing None as node
    TreeSitterTraversal.find_child_by_field(None, "name")
    assert "Error finding child by field name" in caplog.text

def test_get_named_descendants_logs_error(complex_tree, caplog):
    """Test that get_named_descendants logs errors."""
    # Cause an error by passing None as node
    TreeSitterTraversal.get_named_descendants(None, 0, 10)
    assert "Error getting named descendants" in caplog.text

def test_create_cursor_at_point_logs_error(complex_tree, caplog):
    """Test that create_cursor_at_point logs errors."""
    # Cause an error by passing None as node
    TreeSitterTraversal.create_cursor_at_point(None, (0, 0))
    assert "Error creating cursor at point" in caplog.text

def test_find_node_at_point_logs_error(complex_tree, caplog):
    """Test that find_node_at_point logs errors."""
    # Cause an error by passing None as root
    TreeSitterTraversal.find_node_at_point(None, Point(0, 0))
    assert "Error finding node at point" in caplog.text

def test_find_nodes_in_range_logs_error(complex_tree, caplog):
    """Test that find_nodes_in_range logs errors."""
    # Create a range but pass None as root
    range_obj = Range(
        start_point=Point(0, 0),
        end_point=Point(0, 10),
        start_byte=0,
        end_byte=10
    )
    TreeSitterTraversal.find_nodes_in_range(None, range_obj)
    assert "Error finding nodes in range" in caplog.text 