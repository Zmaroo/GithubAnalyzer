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
    
    # Config file
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("key: value")
    
    # Doc file
    md_file = tmp_path / "readme.md"
    md_file.write_text("# Test")
    
    # License file
    license_file = tmp_path / "LICENSE.txt"
    license_file.write_text("MIT License")
    
    yield tmp_path
    
    # Cleanup
    py_file.unlink()
    yaml_file.unlink()
    md_file.unlink()
    license_file.unlink()

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

def test_parse_config_file(parser_service, test_files):
    """Test parsing config file."""
    result = parser_service.parse_file(test_files / "config.yaml")
    assert not result.is_code
    assert result.tree is None
    assert result.language == "config"
    assert "key: value" in result.content

def test_parse_doc_file(parser_service, test_files):
    """Test parsing documentation file."""
    result = parser_service.parse_file(test_files / "readme.md")
    assert not result.is_code
    assert result.tree is None
    assert result.language == "documentation"
    assert "# Test" in result.content

def test_parse_license_file(parser_service, test_files):
    """Test parsing license file."""
    result = parser_service.parse_file(test_files / "LICENSE.txt")
    assert not result.is_code
    assert result.tree is None
    assert result.language == "license"
    assert "MIT License" in result.content

def test_parse_file_no_language(parser_service, test_files):
    """Test parsing file without language specification."""
    test_file = test_files / "test.unknown"
    test_file.write_text("test content")
    try:
        with pytest.raises(ParserError) as exc:
            parser_service.parse_file(test_file)
        assert "Could not detect language for file" in str(exc.value)
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

def test_required_config_fields(parser_service):
    """Test getting required configuration fields."""
    fields = parser_service.get_required_config_fields()
    assert isinstance(fields, list)
    assert "language_bindings" in fields 