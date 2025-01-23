"""Tests for TreeSitterQueryHandler."""

import pytest
from tree_sitter import Query, Node, Tree, Parser, QueryError
from tree_sitter_language_pack import get_binding, get_language
import logging

from src.GithubAnalyzer.core.models.errors import QueryError, LanguageError
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_query import TreeSitterQueryHandler

@pytest.fixture
def query_handler():
    """Create a TreeSitterQueryHandler instance."""
    return TreeSitterQueryHandler()

@pytest.fixture
def python_parser():
    """Create a Python parser using tree-sitter v24 API."""
    binding = get_binding('python')
    language = get_language('python')
    parser = Parser()
    parser.language = language
    return parser

@pytest.fixture
def python_tree(python_parser):
    """Create a Python tree for testing."""
    code = """
def test_function():
    return 42

class TestClass:
    def method(self):
        pass
"""
    return python_parser.parse(bytes(code, "utf8"))

def test_create_query(query_handler):
    """Test query creation and caching."""
    query = query_handler.create_query("python", "(function_definition) @function")
    assert isinstance(query, Query)
    
    # Test caching
    query2 = query_handler.create_query("python", "(function_definition) @function")
    assert query is query2  # Should return cached instance

def test_create_query_errors(query_handler):
    """Test error handling in query creation."""
    # Invalid language should raise LookupError from tree-sitter-language-pack
    with pytest.raises(LookupError):
        query_handler.create_query("invalid_lang", "(function_definition) @function")
    
    # Invalid query should raise QueryError from tree-sitter
    with pytest.raises(QueryError):
        query_handler.create_query("python", "invalid query")

def test_execute_query(query_handler, python_tree):
    """Test query execution returns tree-sitter captures directly."""
    query = query_handler.create_query("python", """
        (function_definition
          name: (identifier) @function.name
        ) @function.definition

        (class_definition
          name: (identifier) @class.name
        ) @class.definition
    """)

    # Test captures() returns dict directly from tree-sitter
    captures = query_handler.execute_query(query, python_tree.root_node)
    assert isinstance(captures, dict)
    assert all(isinstance(node, Node) for nodes in captures.values() for node in nodes)

def test_execute_query_error(query_handler, python_tree):
    """Test error handling in query execution."""
    query = query_handler.create_query("python", "(function_definition) @function")
    
    # None node should raise ValueError
    with pytest.raises(ValueError):
        query_handler.execute_query(query, None)

def test_find_nodes_function(query_handler, python_tree):
    """Test finding function nodes."""
    nodes = query_handler.find_nodes(python_tree, "python", "function")
    assert len(nodes) > 0
    assert all(isinstance(node, Node) for node in nodes)

def test_find_nodes_class(query_handler, python_tree):
    """Test finding class nodes."""
    nodes = query_handler.find_nodes(python_tree, "python", "class")
    assert len(nodes) > 0
    assert all(isinstance(node, Node) for node in nodes)

def test_find_nodes_errors(query_handler, python_tree):
    """Test error handling in find_nodes."""
    # Invalid language should return empty list since pattern will be None
    nodes = query_handler.find_nodes(python_tree, "invalid_lang", "function")
    assert len(nodes) == 0

    # Invalid pattern type should return empty list
    nodes = query_handler.find_nodes(python_tree, "python", "invalid_type")
    assert len(nodes) == 0

def test_find_nodes_with_unicode(query_handler, python_parser):
    """Test finding nodes in code with unicode characters."""
    code = """
def test_unicode():
    return "🐍"
"""
    tree = python_parser.parse(bytes(code, "utf8"))
    nodes = query_handler.find_nodes(tree, "python", "function")
    assert len(nodes) > 0
    assert all(isinstance(node, Node) for node in nodes) 