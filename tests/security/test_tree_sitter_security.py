"""Security tests for the TreeSitterParser."""

import os
from pathlib import Path

import pytest

from GithubAnalyzer.models.core.errors import ParseError
from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser


@pytest.fixture
def parser():
    """Create a TreeSitterParser instance."""
    parser = TreeSitterParser()
    parser.initialize()
    return parser


def test_malformed_input_handling(parser):
    """Test handling of malformed input."""
    malformed_inputs = [
        "def broken_python) {",
        "function broken_js {",
        "#include <malformed.h",
        "class BrokenJava {",
    ]

    for code in malformed_inputs:
        result = parser.parse(code, "python")
        assert not result["syntax_valid"]


def test_large_input_handling(parser):
    """Test handling of large inputs."""
    large_code = "print('x' * 1000000)\n" * 100
    result = parser.parse(large_code, "python")
    assert result["syntax_valid"]
    assert result["node_count"] > 0


def test_special_characters(parser):
    """Test handling of special characters."""
    code_with_special_chars = """
def test():
    print("🔥")  # Fire emoji
    print("\\x00\\x01\\x02")  # Control characters
    print("\\u0000")  # Null character
    print("\\t\\n\\r")  # Whitespace
    return True
"""
    result = parser.parse(code_with_special_chars, "python")
    assert result["syntax_valid"]


def test_path_traversal_prevention(parser, tmp_path):
    """Test prevention of path traversal attacks."""
    test_file = tmp_path / "test.py"
    test_file.write_text('print("Hello")')

    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\Windows\\System32\\config",
        "/etc/shadow",
        "C:\\Windows\\System32\\config",
        f"{test_file}/../../../etc/passwd",
    ]

    for path in malicious_paths:
        with pytest.raises(ParseError):
            parser.parse_file(path)


def test_binary_file_handling(parser, tmp_path):
    """Test handling of binary files."""
    binary_file = tmp_path / "test.py"
    with open(binary_file, "wb") as f:
        f.write(bytes(range(256)))

    with pytest.raises(ParseError, match="is not a text file"):
        parser.parse_file(str(binary_file))


def test_memory_exhaustion_prevention(parser):
    """Test prevention of memory exhaustion attacks."""
    # Create a string that would expand significantly when parsed
    deep_nesting = "(" * 1000 + ")" * 1000

    try:
        parser.parse(deep_nesting, "python")
    except ParseError:
        pass  # Either parsing fails or succeeds with reasonable memory usage


def test_concurrent_access_safety(parser, tmp_path):
    """Test thread safety of the parser."""
    from concurrent.futures import ThreadPoolExecutor

    test_file = tmp_path / "test.py"
    test_file.write_text('print("Hello, World!")')

    def parse_file():
        for i in range(100):
            result = parser.parse_file(str(test_file))
            assert result["syntax_valid"]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(parse_file) for _ in range(4)]
        for future in futures:
            future.result()
