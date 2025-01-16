"""Tests for ParserService."""

import pytest
from pathlib import Path
from typing import Dict, List

from GithubAnalyzer.services.core.parser_service import ParserService
from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.config.language_config import get_language_by_extension

@pytest.fixture
def parser_service() -> ParserService:
    """Create a ParserService instance."""
    service = ParserService()
    service.initialize()
    return service

def test_parser_service_initialization():
    """Test ParserService initialization."""
    service = ParserService()
    service.initialize()
    
    # Check that core parsers are initialized
    assert service._tree_sitter is not None
    assert service._config_parser is not None
    assert service._doc_parser is not None
    assert service._license_parser is not None

def test_parse_file(parser_service, tmp_path):
    """Test parsing different file types."""
    # Create test files
    python_file = tmp_path / "test.py"
    python_file.write_text("def test(): pass")
    
    js_file = tmp_path / "test.js"
    js_file.write_text("function test() {}")
    
    config_file = tmp_path / "config.yaml"
    config_file.write_text("key: value")
    
    # Test parsing each file type
    python_result = parser_service.parse_file(python_file)
    assert python_result.is_valid
    assert "test" in python_result.metadata["analysis"]["functions"]
    
    js_result = parser_service.parse_file(js_file)
    assert js_result.is_valid
    assert "test" in js_result.metadata["analysis"]["functions"]
    
    config_result = parser_service.parse_file(config_file)
    assert config_result.is_valid
    assert "key" in config_result.metadata["data"]

def test_parse_directory(parser_service, tmp_path):
    """Test parsing a directory of files."""
    # Create test directory structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    
    (src_dir / "main.py").write_text("def main(): pass")
    (src_dir / "util.js").write_text("function util() {}")
    (src_dir / "config.yaml").write_text("setting: value")
    
    # Create nested directory
    lib_dir = src_dir / "lib"
    lib_dir.mkdir()
    (lib_dir / "helper.py").write_text("def helper(): return True")
    
    # Test parsing directory
    results = parser_service.parse_directory(src_dir)
    
    # Verify results
    assert len(results) == 4  # All files should be parsed
    
    # Check specific files
    by_path = {str(r.file_path): r for r in results}
    
    main_result = by_path[str(src_dir / "main.py")]
    assert "main" in main_result.metadata["analysis"]["functions"]
    
    util_result = by_path[str(src_dir / "util.js")]
    assert "util" in util_result.metadata["analysis"]["functions"]
    
    helper_result = by_path[str(lib_dir / "helper.py")]
    assert "helper" in helper_result.metadata["analysis"]["functions"]

def test_parse_content():
    """Test parsing content directly."""
    service = ParserService()
    service.initialize()
    
    # Test various content types
    python_content = "def test(): return 42"
    result = service.parse_content(python_content, "python")
    assert result.is_valid
    assert "test" in result.metadata["analysis"]["functions"]
    
    # Test invalid language
    with pytest.raises(ParserError):
        service.parse_content("content", "invalid_lang")
    
    # Test empty content
    empty_result = service.parse_content("", "python")
    assert empty_result.is_valid
    assert not empty_result.metadata["analysis"]["functions"]

def test_get_parser_for_file():
    """Test parser selection logic."""
    service = ParserService()
    service.initialize()
    
    # Test known extensions
    py_parser = service._get_parser_for_file(Path("test.py"))
    assert py_parser is service._tree_sitter
    
    yaml_parser = service._get_parser_for_file(Path("test.yaml"))
    assert yaml_parser is service._config_parser
    
    # Test unknown extension
    with pytest.raises(ParserError):
        service._get_parser_for_file(Path("test.unknown"))

def test_parse_with_options():
    """Test parsing with custom options."""
    service = ParserService()
    service.initialize()
    
    content = "def test(): pass"
    options = {"debug": True, "include_comments": True}
    
    result = service.parse_content(content, "python", options=options)
    assert result.is_valid
    assert result.metadata["analysis"]["functions"]
    
    # Test invalid options
    with pytest.raises(ValueError):
        service.parse_content(content, "python", options={"invalid": True}) 