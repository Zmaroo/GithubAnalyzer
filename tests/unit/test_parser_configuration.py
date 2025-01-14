"""Test parser service configuration.

This module contains tests for verifying configuration handling
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
        Uninitialized TreeSitterParser instance.
    """
    return TreeSitterParser()


def test_parser_default_configuration(parser: TreeSitterParser) -> None:
    """Test parser service default configuration.

    Tests:
        - Default initialization behavior
        - All supported languages loaded
    """
    parser.initialize()
    assert parser.initialized

    # Check all supported languages are loaded
    expected_languages = {
        "python",
        "javascript",
        "typescript",
        "java",
        "cpp",
        "rust",
        "go",
        "ruby",
        "php",
        "c",
        "csharp",
        "scala",
        "kotlin",
        "lua",
        "bash",
        "html",
        "css",
        "json",
        "yaml",
        "toml",
        "xml",
        "markdown",
        "sql",
        "arduino",
        "cmake",
        "cuda",
        "groovy",
        "matlab",
    }
    assert set(parser._parsers.keys()) == expected_languages
    assert set(parser._languages.keys()) == expected_languages


def test_parser_custom_language_configuration(parser: TreeSitterParser) -> None:
    """Test parser service custom language configuration.

    Tests:
        - Initialization with subset of languages
        - Only specified languages loaded
    """
    custom_languages = ["python", "javascript", "typescript"]
    parser.initialize(custom_languages)
    assert parser.initialized
    assert set(parser._parsers.keys()) == set(custom_languages)
    assert set(parser._languages.keys()) == set(custom_languages)


def test_parser_invalid_language_configuration(parser: TreeSitterParser) -> None:
    """Test parser service invalid language configuration.

    Tests:
        - Error handling for invalid language configuration
        - Parser state after failed initialization
    """
    with pytest.raises(ParseError, match="Language invalid_lang not supported"):
        parser.initialize(["python", "invalid_lang"])
    assert not parser.initialized
    assert len(parser._parsers) == 0
    assert len(parser._languages) == 0
