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
from GithubAnalyzer.analysis.models.tree_sitter import TreeSitterEdit

@pytest.fixture(autouse=True)
def setup_logging(caplog):
    """Set up logging configuration for tests."""
    caplog.set_level(logging.DEBUG)
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "GithubAnalyzer": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": True
            }
        }
    }
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

    with pytest.raises(ParserError, match="Unsupported file type"):
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
    # Test initialization logging
    parser.initialize(["python"])
    assert any("Initializing parser with languages" in record.message for record in caplog.records)

    # Test file parsing logging
    test_file = test_files / "test.py"
    test_file.write_text("def test(): pass")
    file_info = file_service.get_file_info(test_file)
    parser.parse_file(file_info)
    assert any("Parsing python content" in record.message for record in caplog.records)

def test_parser_debug_logging(parser: TreeSitterParser, test_files: Path, file_service: FileService, caplog) -> None:
    """Test detailed debug logging."""
    # Enable debug logging
    parser.set_debug(True)
    parser.initialize(["python"])

    # Parse a file with syntax error
    error_file = test_files / "error.py"
    error_file.write_text("def invalid_syntax(:")

    file_info = file_service.get_file_info(error_file)
    try:
        parser.parse_file(file_info)
    except ParserError:
        pass

    # Check for debug messages
    debug_messages = [
        record.message for record in caplog.records 
        if record.levelname == 'DEBUG' and '[tree-sitter]' in record.message
    ]
    assert len(debug_messages) > 0, "No tree-sitter debug messages found"
    assert any("Starting parse" in msg for msg in debug_messages), "Missing parse start message"
    assert any("Initialized language: python" in msg for msg in debug_messages), "Missing language initialization message"

def test_edit_file(parser: TreeSitterParser, test_files: Path, file_service: FileService) -> None:
    """Test editing a previously parsed file."""
    parser.initialize(["python"])
    
    # Create and parse initial file
    test_file = test_files / "edit_test.py"
    test_file.write_text("def original(): return 42")
    file_info = file_service.get_file_info(test_file)
    
    # Parse and cache the initial AST
    original_result = parser.parse_file(file_info)
    assert original_result.success
    assert "original" in original_result.ast.root_node.text.decode()
    
    # Get the cache key format
    cache_key = str(test_file.resolve())
    
    # Create an edit operation
    edit = TreeSitterEdit(
        start_byte=4,  # Start at 'o' in 'original'
        old_end_byte=12,  # End at 'l' in 'original'
        new_end_byte=11,  # New length for 'modified'
        start_point=(0, 4),  # Line 0, column 4
        old_end_point=(0, 12),  # Line 0, column 12
        new_end_point=(0, 11)  # Line 0, column 11
    )
    
    # Apply the edit
    parser.edit_file(test_file, edit)
    
    # Verify the changes were tracked
    assert cache_key in parser._changed_files
    
    # Write the modified content
    test_file.write_text("def modified(): return 42")
    
    # Parse the modified file
    modified_result = parser.parse_file(file_info)
    assert modified_result.success
    assert "modified" in modified_result.ast.root_node.text.decode()
    assert "original" not in modified_result.ast.root_node.text.decode()
    
    # Verify that parsing again clears the changed flag
    assert cache_key not in parser._changed_files
