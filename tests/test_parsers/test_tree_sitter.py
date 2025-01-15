"""Tests for the TreeSitterParser."""

from pathlib import Path
from typing import Generator

import pytest

from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.models.analysis.ast import ParseResult
from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser


@pytest.fixture
def parser() -> Generator[TreeSitterParser, None, None]:
    """Create a TreeSitterParser instance."""
    parser = TreeSitterParser()
    # Initialize all languages needed for tests
    parser.initialize([
        "python", "javascript", "typescript",
        "css", "yaml", "json", "bash", "cpp",
        "java", "html"
    ])
    yield parser
    parser.cleanup()


def test_initialization(parser: TreeSitterParser) -> None:
    """Test parser initialization."""
    assert parser.initialized
    assert len(parser._parsers) > 0
    assert len(parser._languages) > 0


def test_language_detection(parser: TreeSitterParser) -> None:
    """Test language detection from file extensions."""
    test_cases = {
        "test.py": "python",
        "main.js": "javascript",
        "style.css": "css",
        "config.yaml": "yaml",
        "data.json": "json",
        "script.sh": "bash",
        "code.cpp": "cpp",
        "app.java": "java",
        "index.html": "html",
        "app.ts": "typescript",
        "component.tsx": "typescript"
    }

    for file_path, expected_lang in test_cases.items():
        detected = parser._get_language_for_file(Path(file_path))
        assert (
            detected == expected_lang
        ), f"Failed to detect {expected_lang} for {file_path}"


def test_parse_python(parser: TreeSitterParser) -> None:
    """Test parsing Python code."""
    content = """
def hello():
    print("Hello, World!")
    return 42
"""
    result = parser.parse(content, "python")
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert result.node_count > 0


def test_parse_javascript(parser: TreeSitterParser) -> None:
    """Test parsing JavaScript code."""
    content = """
function hello() {
    console.log("Hello, World!");
    return 42;
}
"""
    result = parser.parse(content, "javascript")
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert result.node_count > 0


def test_parse_invalid_syntax(parser: TreeSitterParser) -> None:
    """Test parsing invalid syntax."""
    content = """
def invalid_python)
    print("This is not valid Python"
"""
    result = parser.parse(content, "python")
    assert isinstance(result, ParseResult)
    assert not result.is_valid


def test_parse_unsupported_language(parser: TreeSitterParser) -> None:
    """Test parsing with unsupported language."""
    with pytest.raises(ParserError, match="Language invalid_lang not supported"):
        parser.parse("some content", "invalid_lang")


def test_parse_file(parser: TreeSitterParser, tmp_path: Path) -> None:
    """Test parsing a file."""
    test_file = tmp_path / "test.py"
    test_file.write_text('print("Hello, World!")')

    result = parser.parse_file(test_file)
    assert isinstance(result, ParseResult)
    assert result.is_valid
    assert result.line_count == 1


def test_parse_invalid_file_type(parser: TreeSitterParser, tmp_path: Path) -> None:
    """Test parsing a file with unsupported extension."""
    test_file = tmp_path / "test.xyz"
    test_file.write_text("some content")

    with pytest.raises(ParserError, match=r".*Unsupported file extension.*"):
        parser.parse_file(test_file)


def test_parse_binary_file(parser: TreeSitterParser, tmp_path: Path) -> None:
    """Test parsing a binary file."""
    test_file = tmp_path / "test.py"
    # Create a proper binary file
    with open(test_file, 'wb') as f:
        f.write(bytes(range(256)))  # Write all possible byte values
    
    with pytest.raises(ParserError, match=r".*not a text file.*"):
        parser.parse_file(test_file)


def test_multiple_languages(parser: TreeSitterParser) -> None:
    """Test parsing multiple languages in sequence."""
    test_cases = {
        "python": "def test(): pass",
        "javascript": "function test() { }",
        # Only test languages we've initialized
        "typescript": "function test(): void { }"
    }

    for lang, code in test_cases.items():
        result = parser.parse(code, lang)
        assert isinstance(result, ParseResult)
        assert result.is_valid
        assert result.node_count > 0
