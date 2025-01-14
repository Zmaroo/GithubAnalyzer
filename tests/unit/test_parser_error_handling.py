"""Test parser service error handling.

This module contains tests for verifying error handling
of the parser service component.
"""

from pathlib import Path

import pytest

from GithubAnalyzer.models.core.errors import ParseError
from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser


@pytest.fixture
def parser() -> TreeSitterParser:
    """Create a TreeSitterParser instance.

    Returns:
        Initialized TreeSitterParser instance.
    """
    parser = TreeSitterParser()
    parser.initialize()
    yield parser
    parser.cleanup()


def test_parser_uninitialized_error() -> None:
    """Test error handling when parser is not initialized."""
    parser = TreeSitterParser()
    with pytest.raises(ParseError, match="Parser not initialized"):
        parser.parse("def test(): pass", "python")


def test_parser_invalid_language(parser: TreeSitterParser) -> None:
    """Test error handling for invalid language."""
    with pytest.raises(ParseError, match="Language invalid_lang not supported"):
        parser.parse("some code", "invalid_lang")


def test_parser_invalid_file_path(parser: TreeSitterParser) -> None:
    """Test error handling for invalid file path."""
    with pytest.raises(ParseError, match="File .* not found"):
        parser.parse_file(Path("nonexistent.py"))


def test_parser_invalid_file_type(parser: TreeSitterParser, tmp_path: Path) -> None:
    """Test error handling for invalid file type."""
    test_file = tmp_path / "test.xyz"
    test_file.write_text("some content")
    with pytest.raises(ParseError, match="Unsupported file extension: .xyz"):
        parser.parse_file(test_file)


def test_parser_binary_file(parser: TreeSitterParser, tmp_path: Path) -> None:
    """Test error handling for binary file."""
    test_file = tmp_path / "test.py"
    test_file.write_bytes(b"\x00\x01\x02\x03")
    with pytest.raises(ParseError, match="is not a text file"):
        parser.parse_file(test_file)


def test_parser_invalid_syntax(parser: TreeSitterParser) -> None:
    """Test error handling for invalid syntax."""
    invalid_code = """
    def invalid_python)
        print("This is not valid Python"
    """
    result = parser.parse(invalid_code, "python")
    assert not result.is_valid
