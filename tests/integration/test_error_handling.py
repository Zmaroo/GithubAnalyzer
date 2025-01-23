"""Test error handling."""
import pytest
from pathlib import Path
from tree_sitter import Parser, Tree, Language

from src.GithubAnalyzer.core.models.errors import (
    ParserError,
    LanguageError,
    QueryError,
    FileOperationError
)
from src.GithubAnalyzer.core.services.file_service import FileService
from src.GithubAnalyzer.core.services.parser_service import ParserService

def test_file_operation_error(file_service):
    """Test file operation error handling."""
    with pytest.raises(FileOperationError) as exc:
        file_service.get_file_info(Path("nonexistent.py"))
    assert "File not found" in str(exc.value)

def test_language_error(file_service):
    """Test language error handling."""
    path = Path("test.unknown")
    path.touch()
    try:
        with pytest.raises(LanguageError) as exc:
            file_service.get_file_info(path)
        assert "Language not supported" in str(exc.value)
    finally:
        path.unlink()

def test_language_error_from_parser(parser_service):
    """Test language error handling in parser service."""
    with pytest.raises(LanguageError) as exc:
        parser_service.parse_content("def test(): pass", "invalid_language")
    assert "Language not supported" in str(exc.value)

def test_parser_error_invalid_syntax(parser_service):
    """Test parser error handling with invalid syntax."""
    invalid_code = "def test() invalid syntax"
    with pytest.raises(ParserError) as exc:
        parser_service.parse_content(invalid_code, "python")
    assert "Syntax errors found" in str(exc.value)
    assert "ERROR at line" in str(exc.value)

def test_parser_tree_attributes(parser_service):
    """Test tree-sitter tree attributes."""
    code = "def test(): pass"
    result = parser_service.parse_content(code, "python")
    
    assert result.tree is not None
    assert result.language == "python"
    assert result.is_code
    assert result.content == code
    
    # Test root node properties
    root = result.tree.root_node
    assert root.type == "module"
    assert root.start_byte == 0
    assert root.end_byte == len(code)
    assert not root.has_error

def test_parser_timeout(parser_service):
    """Test parser timeout handling."""
    # Create a very long string that might timeout
    long_code = "def test():\n" + "    pass\n" * 10000
    
    # Create a new parser service with a very short timeout
    timeout_parser = ParserService(timeout_micros=1)
    
    with pytest.raises(ParserError) as exc:
        timeout_parser.parse_content(long_code, "python")
    assert "Failed to parse" in str(exc.value)

def test_parser_encoding(parser_service):
    """Test parser handles different encodings."""
    # Test with special characters
    code = "def test_unicode():\n    return '🐍'"
    result = parser_service.parse_content(code, "python")
    assert result.is_code
    assert result.tree is not None
    assert not result.tree.root_node.has_error

def test_syntax_error_details(parser_service):
    """Test detailed syntax error reporting."""
    invalid_code = """
def test():
    if True
        print('missing colon')
    """
    with pytest.raises(ParserError) as exc:
        parser_service.parse_content(invalid_code, "python")
    error_msg = str(exc.value)
    assert "Syntax errors found" in error_msg
    assert "ERROR at line" in error_msg 