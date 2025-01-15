"""Test parser service initialization.

This module contains tests for verifying proper initialization
of the parser service component.
"""

from typing import Generator

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


def test_parser_initialization(parser: TreeSitterParser) -> None:
    """Test basic initialization."""
    assert not parser.initialized
    parser.initialize(["python"])  # Start with just Python
    assert parser.initialized
    assert "python" in parser._parsers
    assert "python" in parser._languages


def test_parser_initialization_with_languages(parser: TreeSitterParser) -> None:
    """Test parser initialization with specific languages.

    Tests:
        - Initialization with subset of languages
        - Language availability after initialization
    """
    languages = ["python", "javascript", "typescript"]
    parser.initialize(languages)
    assert parser.initialized
    assert set(parser._parsers.keys()) == set(languages)
    assert set(parser._languages.keys()) == set(languages)


def test_parser_initialization_invalid_language(parser: TreeSitterParser) -> None:
    """Test parser initialization with invalid language.

    Tests:
        - Error handling for unsupported languages
    """
    with pytest.raises(ParseError, match="Language invalid_lang not supported"):
        parser.initialize(["python", "invalid_lang"])
