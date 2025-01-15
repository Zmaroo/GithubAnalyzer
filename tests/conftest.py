"""Test configuration."""

from typing import Generator
import pytest

from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser

@pytest.fixture(scope="session")
def tree_sitter_parser() -> Generator[TreeSitterParser, None, None]:
    """Create shared TreeSitterParser instance."""
    parser = TreeSitterParser()
    try:
        parser.initialize(["python"])
        yield parser
    finally:
        parser.cleanup()
