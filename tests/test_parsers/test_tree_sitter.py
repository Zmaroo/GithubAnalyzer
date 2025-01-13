import pytest
from GithubAnalyzer.parsers.tree_sitter import TreeSitterParser

def test_parser_initialization():
    parser = TreeSitterParser()
    assert parser is not None
    assert parser.parser is not None

def test_parse_python_file(sample_python_file):
    parser = TreeSitterParser()
    with open(sample_python_file) as f:
        content = f.read()
    result = parser.parse_file(str(sample_python_file), content)
    
    assert result.success
    assert result.ast is not None
    assert not result.errors 