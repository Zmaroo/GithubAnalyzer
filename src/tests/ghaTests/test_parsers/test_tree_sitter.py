"""Tests for the tree-sitter parser.

This module contains tests for verifying proper functionality
of the tree-sitter parser component.
"""

import pytest
import logging
from pathlib import Path
from typing import Generator, List
from unittest.mock import MagicMock

from GithubAnalyzer import TreeSitterParser
from GithubAnalyzer.core.models.errors import ParserError
from GithubAnalyzer.core.models.file import FileInfo, FileType
from GithubAnalyzer.core.services.file_service import FileService
from GithubAnalyzer.core.config.logging_config import get_logging_config

@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging configuration for tests."""
    config = get_logging_config()
    logging.config.dictConfig(config)

@pytest.fixture
def test_files(tmp_path: Path) -> Generator[Path, None, None]:
    """Create temporary test files."""
    # Python test file
    python_file = tmp_path / "test.py"
    python_file.write_text("""
def hello():
    print("Hello, World!")
    return 42
""")
    
    # JavaScript test file
    js_file = tmp_path / "test.js"
    js_file.write_text("""
function hello() {
    console.log("Hello, World!");
    return 42;
}
""")
    
    yield tmp_path

@pytest.fixture
def parser() -> Generator[TreeSitterParser, None, None]:
    """Create a TreeSitterParser instance."""
    parser = TreeSitterParser()
    yield parser
    parser.cleanup()

@pytest.fixture
def file_service() -> FileService:
    """Create a FileService instance."""
    return FileService()

def test_parser_initialization(parser: TreeSitterParser) -> None:
    """Test parser initialization with file service."""
    parser.initialize(["python", "javascript"])
    assert parser.initialized
    assert "python" in parser.supported_languages
    assert "javascript" in parser.supported_languages

def test_parse_python_file(parser: TreeSitterParser, test_files: Path, file_service: FileService) -> None:
    """Test parsing Python file."""
    parser.initialize(["python"])
    file_info = file_service.get_file_info(test_files / "test.py")
    
    result = parser.parse_file(file_info)
    assert result.success
    assert result.ast is not None
    assert result.language == "python"
    assert "hello" in result.ast.root_node.text.decode()

def test_parse_javascript_file(parser: TreeSitterParser, test_files: Path, file_service: FileService) -> None:
    """Test parsing JavaScript file."""
    parser.initialize(["javascript"])
    file_info = file_service.get_file_info(test_files / "test.js")
    
    result = parser.parse_file(file_info)
    assert result.success
    assert result.ast is not None
    assert result.language == "javascript"
    assert "hello" in result.ast.root_node.text.decode()

def test_parse_unsupported_language(parser: TreeSitterParser, test_files: Path, file_service: FileService) -> None:
    """Test parsing file with unsupported language."""
    parser.initialize(["python"])
    
    # Create a file with unsupported extension
    unsupported_file = test_files / "test.xyz"
    unsupported_file.write_text("test")
    file_info = file_service.get_file_info(unsupported_file)
    
    with pytest.raises(ParserError, match="Language not supported"):
        parser.parse_file(file_info)

def test_parse_invalid_file(parser: TreeSitterParser, file_service: FileService) -> None:
    """Test parsing invalid/nonexistent file."""
    parser.initialize(["python"])
    file_info = FileInfo(
        path=Path("nonexistent.py"),
        file_type=FileType.PYTHON,
        size=0,
        is_binary=False
    )
    
    with pytest.raises(ParserError):
        parser.parse_file(file_info)

def test_cleanup(parser: TreeSitterParser) -> None:
    """Test parser cleanup."""
    parser.initialize(["python", "javascript"])
    assert parser.initialized
    
    parser.cleanup()
    assert not parser.initialized

def test_parser_logging(parser: TreeSitterParser, test_files: Path, file_service: FileService, caplog) -> None:
    """Test parser logging functionality."""
    caplog.set_level(logging.DEBUG)
    
    # Test initialization logging
    parser.initialize(["python"])
    assert any("Initializing parser" in record.message for record in caplog.records)
    assert any("Loading language: python" in record.message for record in caplog.records)
    
    caplog.clear()
    
    # Test parsing logging
    file_info = file_service.get_file_info(test_files / "test.py")
    result = parser.parse_file(file_info)
    assert any("Parsing python content" in record.message for record in caplog.records)
    assert any("Successfully parsed" in record.message for record in caplog.records)
    
    caplog.clear()
    
    # Test error logging
    invalid_file = FileInfo(
        path=Path("nonexistent.py"),
        file_type=FileType.PYTHON,
        size=0,
        is_binary=False
    )
    try:
        parser.parse_file(invalid_file)
    except ParserError:
        pass
    assert any("Error parsing file" in record.message for record in caplog.records)

def test_parser_debug_logging(parser: TreeSitterParser, test_files: Path, file_service: FileService, caplog) -> None:
    """Test detailed debug logging."""
    caplog.set_level(logging.DEBUG)
    
    # Enable debug logging
    parser.set_debug(True)
    
    # Parse a file with syntax error
    error_file = test_files / "error.py"
    error_file.write_text("def invalid_syntax(:")
    
    file_info = file_service.get_file_info(error_file)
    try:
        parser.parse_file(file_info)
    except ParserError:
        pass
        
    assert any("[tree-sitter] debug:" in record.message for record in caplog.records)
    assert any("Syntax error" in record.message for record in caplog.records)
    
    # Test disabling debug logging
    caplog.clear()
    parser.set_debug(False)
    
    try:
        parser.parse_file(file_info)
    except ParserError:
        pass
        
    assert not any("[tree-sitter] debug:" in record.message for record in caplog.records)
