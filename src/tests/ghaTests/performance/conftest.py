"""Performance test configuration."""

import pytest
from GithubAnalyzer.services.core.parsers import TreeSitterParser

@pytest.fixture(scope="session")
def performance_parser():
    """Create parser for performance tests."""
    parser = TreeSitterParser()
    parser.initialize()
    yield parser
    parser.cleanup() 