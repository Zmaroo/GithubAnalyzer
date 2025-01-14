"""Test parser service cleanup.

This module contains tests for verifying cleanup operations
of the parser service component.
"""

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
    return parser


def test_parser_cleanup(parser: TreeSitterParser) -> None:
    """Test parser service cleanup.

    Tests:
        - Parser state before cleanup
        - Parser state after cleanup
        - Parser reinitialization after cleanup
    """
    # Verify initial state
    assert parser.initialized
    assert len(parser._parsers) > 0
    assert len(parser._languages) > 0

    # Perform cleanup
    parser.cleanup()
    assert not parser.initialized
    assert len(parser._parsers) == 0
    assert len(parser._languages) == 0

    # Verify parser can be reinitialized
    parser.initialize()
    assert parser.initialized
    assert len(parser._parsers) > 0
    assert len(parser._languages) > 0


def test_parser_cleanup_uninitialized() -> None:
    """Test cleanup of uninitialized parser.

    Tests:
        - Cleanup operation on uninitialized parser
        - Parser state after cleanup
    """
    parser = TreeSitterParser()
    assert not parser.initialized
    parser.cleanup()  # Should not raise any errors
    assert not parser.initialized
    assert len(parser._parsers) == 0
    assert len(parser._languages) == 0


def test_parser_operations_after_cleanup(parser: TreeSitterParser) -> None:
    """Test parser operations after cleanup.

    Tests:
        - Error handling for operations on cleaned up parser
        - Parser state after cleanup
    """
    parser.cleanup()
    with pytest.raises(ParseError, match="Parser not initialized"):
        parser.parse("def test(): pass", "python")
