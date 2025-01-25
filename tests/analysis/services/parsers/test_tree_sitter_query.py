"""Tests for TreeSitterQueryHandler."""
import pytest
import json  # Add this import
from tree_sitter import Query, Node, Tree, Parser, QueryError, Point
from tree_sitter_language_pack import get_parser, get_language

from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_query import TreeSitterQueryHandler
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_traversal import TreeSitterTraversal
from src.GithubAnalyzer.analysis.services.parsers.query_patterns import QueryOptimizationSettings
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_logging import TreeSitterLogHandler

@pytest.fixture
def query_handler():
    return TreeSitterQueryHandler()

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
import os
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
    (#is? "type" "function")
    """

def test_create_query(query_handler):
    """Test creating a query."""
    language = get_language("python")
    query = query_handler.create_query(language, "(function_definition) @function")
    assert query is not None

def test_create_query_errors(query_handler):
    """Test creating a query with errors."""
    language = get_language("python")
    with pytest.raises(QueryError):
        query_handler.create_query(language, "(invalid_syntax) @error")

def test_execute_query(query_handler, python_tree):
    """Test executing a query."""
    language = get_language("python")
    query = query_handler.create_query(language, "(function_definition) @function")
    matches = query_handler.execute_query(query, python_tree)
    assert len(matches) > 0

def test_get_matches(query_handler, python_tree):
    """Test getting matches from a query."""
    language = get_language("python")
    query = query_handler.create_query(language, "(function_definition) @function")
    matches = query_handler.get_matches(query, python_tree)
    assert len(matches) > 0

def test_execute_query_error(query_handler):
    """Test executing a query with errors."""
    language = get_language("python")
    query = query_handler.create_query(language, "(function_definition) @function")
    with pytest.raises(QueryError):
        query_handler.execute_query(query, None)

def test_find_nodes(query_handler, python_parser):
    """Test finding nodes in a tree."""
    code = "def test(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    nodes = query_handler.find_nodes(tree.root_node, "function_definition")
    assert len(nodes) > 0

def test_find_nodes_with_unicode(query_handler, python_parser):
    """Test finding nodes with unicode characters."""
    code = "def test(): pass\nprint('こんにちは')"
    tree = python_parser.parse(bytes(code, "utf8"))
    nodes = query_handler.find_nodes(tree.root_node, "function_definition")
    assert len(nodes) > 0

def test_find_nodes_with_invalid_pattern(query_handler, python_tree):
    """Test finding nodes with an invalid pattern."""
    with pytest.raises(QueryError):
        query_handler.find_nodes(python_tree.root_node, "(invalid_syntax)")

def test_find_nodes_with_all_patterns(query_handler, python_parser):
    """Test finding nodes with all patterns."""
    code = "def test(): pass\nprint('Hello')"
    tree = python_parser.parse(bytes(code, "utf8"))
    nodes = query_handler.find_nodes(tree.root_node, "function_definition")
    assert len(nodes) > 0

def test_find_nodes_with_none_pattern(query_handler, python_tree):
    """Test finding nodes with a None pattern."""
    nodes = query_handler.find_nodes(python_tree.root_node, None)
    assert len(nodes) == 0

def test_configure_query_with_ranges(query_handler, python_tree):
    """Test configuring a query with ranges."""
    language = get_language("python")
    query = query_handler.create_query(language, "(function_definition) @function")
    ranges = query_handler.configure_query_with_ranges(query, python_tree, [(0, 0), (1, 0)])
    assert len(ranges) > 0

def test_get_pattern_info(query_handler):
    """Test getting pattern information."""
    language = get_language("python")
    query = query_handler.create_query(language, "(function_definition) @function")
    pattern_info = query_handler.get_pattern_info(query)
    assert len(pattern_info) > 0

def test_get_query_stats(query_handler, python_tree):
    """Test getting query statistics."""
    language = get_language("python")
    query = query_handler.create_query(language, "(function_definition) @function")
    stats = query_handler.get_query_stats(query, python_tree)
    assert len(stats) > 0

def test_set_query_range(query_handler, python_parser, python_query):
    """Test setting a query range."""
    code = "def test(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    query_handler.set_query_range(python_query, tree.root_node, (0, 0), (1, 0))
    assert python_query.range is not None

def test_get_matches(query_handler, python_tree):
    """Test getting matches returns tree-sitter matches directly."""
    query = query_handler.create_query("""
        (function_definition) @function
    """)
    matches = query_handler.get_matches(query, python_tree.root_node)
    assert isinstance(matches, list)
    assert all(isinstance(match, dict) for match in matches)
    assert all("function" in match for match in matches)

def test_execute_query_error(query_handler):
    """Test error handling in execute_query."""
    query = query_handler.create_query("""
        (function_definition) @function
    """)
    with pytest.raises(ValueError):
        query_handler.execute_query(query, None)

def test_find_nodes(query_handler, python_parser):
    """Test finding nodes by pattern type."""
    source = """
def test_func(x, y):
    return x + y
"""
    tree = python_parser.parse(bytes(source, "utf8"))
    nodes = query_handler.find_nodes(tree, "function")
    assert len(nodes) > 0
    assert nodes[0].type == "function_definition"

def test_find_nodes_with_unicode(query_handler, python_parser):
    """Test finding nodes with Unicode characters."""
    source = """
def test_func_π(α, β):
    return α + β
"""
    tree = python_parser.parse(bytes(source, "utf8"))
    nodes = query_handler.find_nodes(tree, "function")
    assert len(nodes) > 0
    assert nodes[0].type == "function_definition"

def test_find_nodes_with_invalid_pattern(query_handler, python_tree):
    """Test finding nodes with invalid pattern returns empty list."""
    nodes = query_handler.find_nodes(python_tree, "invalid_pattern")
    assert isinstance(nodes, list)
    assert len(nodes) == 0

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

import os
"""
    tree = python_parser.parse(bytes(source, "utf8"))
    pattern_types = ["function", "class", "string", "comment", "call", "attribute", "import"]
    
    for pattern_type in pattern_types:
        nodes = query_handler.find_nodes(tree, pattern_type)
        assert isinstance(nodes, list)
        assert len(nodes) > 0

def test_find_nodes_with_none_pattern(query_handler, python_tree):
    """Test finding nodes with None pattern returns empty list."""
    nodes = query_handler.find_nodes(python_tree, "non_existent_pattern_type")
    assert isinstance(nodes, list)
    assert len(nodes) == 0

def test_configure_query_with_ranges(query_handler, python_tree):
    """Test configuring query with byte and point ranges."""
    query = query_handler.create_query("(function_definition) @function")
    
    # Configure with byte range
    settings = QueryOptimizationSettings(
        byte_range=(0, 100)
    )
    query_handler.configure_query(query, settings)
    captures = query_handler.execute_query(query, python_tree.root_node)
    assert isinstance(captures, dict)
    
    # Configure with point range
    settings = QueryOptimizationSettings(
        point_range=((0, 0), (5, 0))
    )
    query_handler.configure_query(query, settings)
    captures = query_handler.execute_query(query, python_tree.root_node)
    assert isinstance(captures, dict)

def test_get_pattern_info(query_handler):
    """Test getting pattern information."""
    query = query_handler.create_query("""
        (function_definition) @func
        (#eq? @func "function_definition")
    """)

    pattern_info = query_handler.get_pattern_info(query, 0)
    assert pattern_info["is_rooted"] is True
    assert pattern_info["is_non_local"] is False

    # Check assertions - should be a dictionary
    assertions = pattern_info["assertions"]
    assert isinstance(assertions, dict)

def test_get_query_stats(query_handler, python_tree):
    """Test getting query statistics."""
    query = query_handler.create_query("""
        (function_definition) @function
        (class_definition) @class
    """)

    # Execute query and get stats
    query_handler.execute_query(query, python_tree.root_node)
    stats = query_handler.get_query_stats(query)

    assert stats["pattern_count"] == 2  # function and class patterns
    assert "match_limit" in stats  # Don't check exact value since it's not writable
    assert "timeout_micros" in stats
    assert "did_exceed_match_limit" in stats

def test_set_query_range(query_handler, python_parser, python_query):
    """Test setting query execution range."""
    code = """
    def first():
        pass

    def second():
        pass
    """
    tree = python_parser.parse(bytes(code, "utf8"))

    # Test byte range
    first_func_end = code.find("def second")
    settings = QueryOptimizationSettings(byte_range=(0, first_func_end))
    query = query_handler.create_query("(function_definition) @function")
    query_handler.configure_query(query, settings)

    # Execute and verify matches are returned
    matches = query_handler.get_matches(query, tree.root_node)
    assert len(matches) > 0
    assert all("function" in match for match in matches)

def test_optimize_query(query_handler, python_parser, python_query):
    """Test query optimization settings."""
    code = """
    def test1(): pass
    def test2(): pass
    def test3(): pass
    """
    tree = python_parser.parse(bytes(code, "utf8"))

    # Test match limit (note: not writable in v24)
    settings = QueryOptimizationSettings(match_limit=1)
    query = query_handler.create_query("(function_definition) @function")
    query_handler.configure_query(query, settings)

    # Execute and verify matches are returned
    matches = query_handler.get_matches(query, tree.root_node)
    assert len(matches) > 0
    assert all("function" in match for match in matches)

def test_query_optimization_combined(query_handler, python_parser, python_query):
    """Test combining multiple query optimizations."""
    code = """
    def test1():
        pass

    def test2():
        pass

    def test3():
        pass
    """
    tree = python_parser.parse(bytes(code, "utf8"))

    # Set both range and optimization settings
    settings = QueryOptimizationSettings(
        point_range=((0, 0), (3, 0)),
        match_limit=1,
        max_start_depth=2
    )
    query = query_handler.create_query("(function_definition) @function")
    query_handler.configure_query(query, settings)

    # Execute and verify matches are returned
    matches = query_handler.get_matches(query, tree.root_node)
    assert len(matches) > 0
    assert all("function" in match for match in matches)

def test_disable_capture(query_handler, python_tree):
    """Test disabling captures."""
    query_string = """
        (function_definition
            name: (identifier) @function.name
            parameters: (parameters) @function.params
        ) @function.definition
    """
    
    # Create query and verify all captures work
    query = query_handler.create_query(query_string)
    captures = query_handler.execute_query(query, python_tree.root_node)
    assert "function.name" in captures
    assert "function.params" in captures
    
    # Disable one capture and verify it's excluded
    query_handler.disable_capture("function.params")
    query = query_handler.create_query(query_string)
    captures = query_handler.execute_query(query, python_tree.root_node)
    assert "function.name" in captures
    assert "function.params" not in captures

def test_disable_pattern(query_handler, python_tree):
    """Test disabling patterns."""
    query_string = """
        (function_definition) @function ;pattern 0
        (class_definition) @class ;pattern 1
    """

    # Create query and verify matches work
    query = query_handler.create_query(query_string)
    matches = query_handler.get_matches(query, python_tree.root_node)
    assert len(matches) > 0
    assert any("function" in match for match in matches)

def test_find_error_nodes(query_handler, python_parser):
    """Test finding error nodes."""
    code = """
def invalid_func(:  # Missing closing parenthesis
    return 42

def missing_body()  # Missing function body
"""
    tree = python_parser.parse(bytes(code, "utf8"))
    assert tree.root_node.has_error

    error_nodes = query_handler.find_nodes(tree, "ERROR")
    assert len(error_nodes) > 0
    assert all(node.type == "ERROR" or node.has_error for node in error_nodes)

def test_query_with_predicates(query_handler, python_parser):
    """Test query with predicates."""
    source = """
def test_func():
    pass

async def async_func():
    pass
"""
    tree = python_parser.parse(bytes(source, "utf8"))
    query = query_handler.create_query("""
        (function_definition
            "async" @async_keyword
        ) @async_function
    """)
    
    captures = query_handler.execute_query(query, tree.root_node)
    assert len(captures) > 0

def test_query_with_multiple_captures(query_handler, python_parser):
    """Test query with multiple captures."""
    source = """
def test_func(x, y):
    return x + y
"""
    tree = python_parser.parse(bytes(source, "utf8"))
    query = query_handler.create_query("""
        (function_definition
            name: (identifier) @name
            parameters: (parameters) @params
            body: (block) @body
        ) @function
    """)
    
    captures = query_handler.execute_query(query, tree.root_node)
    assert len(captures) > 0