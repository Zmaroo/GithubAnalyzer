"""Test configuration."""
import pytest
from typing import Generator
from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "requires_languages: mark test as requiring specific tree-sitter language packages"
    )

@pytest.fixture(scope="session")
def tree_sitter_parser() -> Generator[TreeSitterParser, None, None]:
    """Create shared TreeSitterParser instance.
    
    Note: Requires tree-sitter language packages to be installed.
    Currently supports:
    - Python (>=0.23.6)
    - JavaScript (>=0.23.1)
    - TypeScript (>=0.23.2)
    And many more...
    """
    parser = TreeSitterParser()
    try:
        # Initialize with commonly used languages
        parser.initialize(["python", "javascript", "typescript", "tsx"])
        yield parser
    finally:
        parser.cleanup()
