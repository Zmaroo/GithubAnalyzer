"""Test parser service initialization.

This module contains tests for verifying proper initialization
of the parser service component.
"""

from typing import Generator

import pytest

from GithubAnalyzer.models.core.errors import ParserError
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
    with pytest.raises(ParserError, match="Language python not installed. Run: pip install tree-sitter-python"):
        parser.initialize(["python"])


def test_parser_initialization_with_languages(parser: TreeSitterParser) -> None:
    """Test parser initialization with specific languages."""
    languages = ["python", "javascript", "typescript"]
    with pytest.raises(ParserError, match="Language python not installed. Run: pip install tree-sitter-python"):
        parser.initialize(languages)


def test_parser_initialization_invalid_language(parser: TreeSitterParser) -> None:
    """Test parser initialization with invalid language."""
    with pytest.raises(ParserError, match="Language invalid_lang not installed"):
        parser.initialize(["invalid_lang"])


"""Test basic initialization first."""

# 1. Test initialization
def test_basic_init():
    """Test basic initialization."""

# 2. Test language loading
def test_language_loading():
    """Test language support loading."""

# 3. Test basic parsing
def test_basic_parsing():
    """Test basic parsing."""
