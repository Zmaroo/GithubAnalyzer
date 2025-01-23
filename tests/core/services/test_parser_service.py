"""Test parser service functionality."""

import pytest
from pathlib import Path
from tree_sitter import Tree
from typing import Generator

from src.GithubAnalyzer.core.models.errors import ParserError, LanguageError
from src.GithubAnalyzer.core.models.file import FileInfo
from src.GithubAnalyzer.core.services.parser_service import ParserService

@pytest.fixture
def test_files(tmp_path) -> Generator[Path, None, None]:
    """Create test files for parsing."""
    # Python file
    py_file = tmp_path / "test.py"
    py_file.write_text("def test(): pass")
    
    # YAML file
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("key: value")
    
    # Markdown file
    md_file = tmp_path / "readme.md"
    md_file.write_text("# Test")
    
    # Text file
    txt_file = tmp_path / "LICENSE.txt"
    txt_file.write_text("MIT License")
    
    yield tmp_path
    
    # Cleanup
    py_file.unlink()
    yaml_file.unlink()
    md_file.unlink()
    txt_file.unlink()

def test_parse_file_with_path(parser_service, test_files):
    """Test parsing file using Path object."""
    result = parser_service.parse_file(test_files / "test.py")
    assert result.is_code
    assert isinstance(result.tree, Tree)
    assert result.language == "python"
    assert "def test()" in result.content

def test_parse_file_with_str(parser_service, test_files):
    """Test parsing file using string path."""
    result = parser_service.parse_file(str(test_files / "test.py"))
    assert result.is_code
    assert isinstance(result.tree, Tree)
    assert result.language == "python"

def test_parse_file_with_file_info(parser_service, test_files):
    """Test parsing file using FileInfo object."""
    file_info = FileInfo(
        path=test_files / "test.py",
        language="python",
        metadata={"size": 0, "extension": ".py"}
    )
    result = parser_service.parse_file(file_info)
    assert result.is_code
    assert isinstance(result.tree, Tree)
    assert result.language == "python"

def test_parse_yaml_file(parser_service, test_files):
    """Test parsing YAML file."""
    result = parser_service.parse_file(test_files / "config.yaml")
    assert result.is_code
    assert isinstance(result.tree, Tree)
    assert result.language == "yaml"
    assert "key: value" in result.content

def test_parse_markdown_file(parser_service, test_files):
    """Test parsing Markdown file."""
    result = parser_service.parse_file(test_files / "readme.md")
    assert result.is_code
    assert isinstance(result.tree, Tree)
    assert result.language == "markdown"
    assert "# Test" in result.content

def test_parse_unsupported_file(parser_service, test_files):
    """Test parsing an unsupported file type."""
    test_file = test_files / "test.txt"
    test_file.write_text("This is a text file")

    result = parser_service.parse_file(test_file)
    assert result.language == "unknown"
    assert not result.is_code
    assert result.tree is None

def test_parse_file_no_language(parser_service, test_files):
    """Test parsing file without language specification."""
    test_file = test_files / "test.unknown"
    test_file.write_text("test content")
    try:
        result = parser_service.parse_file(test_file)
        assert not result.is_code
        assert result.tree is None
        assert result.language == "unknown"
        assert "test content" in result.content
    finally:
        test_file.unlink()

def test_parse_file_invalid_path(parser_service):
    """Test parsing non-existent file."""
    with pytest.raises(ParserError) as exc:
        parser_service.parse_file("nonexistent.py")
    assert "Failed to parse file" in str(exc.value)

def test_parse_file_with_timeout(test_files):
    """Test parsing file with timeout configuration."""
    # Create parser with very short timeout
    parser_service = ParserService(timeout_micros=1)
    
    # Create a large file
    large_file = test_files / "large.py"
    large_file.write_text("def test():\n" + "    pass\n" * 10000)
    
    try:
        with pytest.raises(ParserError) as exc:
            parser_service.parse_file(large_file)
        assert "Failed to parse" in str(exc.value)
    finally:
        large_file.unlink()

def test_parse_file_with_syntax_error(parser_service, test_files):
    """Test parsing file with syntax error."""
    # Create file with syntax error
    error_file = test_files / "error.py"
    error_file.write_text("def test() syntax error")
    
    try:
        with pytest.raises(ParserError) as exc:
            parser_service.parse_file(error_file)
        assert "Syntax errors found" in str(exc.value)
        assert "ERROR at line" in str(exc.value)
    finally:
        error_file.unlink()

def test_parse_file_with_unicode(parser_service, test_files):
    """Test parsing file with unicode characters."""
    # Create file with unicode
    unicode_file = test_files / "unicode.py"
    unicode_file.write_text('def test():\n    return "🐍"')
    
    try:
        result = parser_service.parse_file(unicode_file)
        assert result.is_code
        assert isinstance(result.tree, Tree)
        assert not result.tree.root_node.has_error
        assert "🐍" in result.content
    finally:
        unicode_file.unlink()

def test_parser_tree_attributes(parser_service):
    """Test tree-sitter tree attributes."""
    code = "def test(): pass"
    result = parser_service.parse_content(code, "python")
    
    assert result.is_code
    assert isinstance(result.tree, Tree)
    assert result.tree.root_node is not None
    assert result.tree.root_node.type == "module"
    assert not result.tree.root_node.has_error
    assert result.language == "python" 