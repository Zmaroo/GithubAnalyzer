import pytest
from GithubAnalyzer.core.parsers.tree_sitter import TreeSitterParser

def test_parser_initialization():
    parser = TreeSitterParser()
    assert parser is not None
    assert parser.parser is not None

def test_parse_python_file(sample_python_file):
    parser = TreeSitterParser()
    with open(sample_python_file) as f:
        result = parser.parse(f.read())
    
    assert result.success
    assert result.tree_sitter_node is not None
    assert not result.errors 