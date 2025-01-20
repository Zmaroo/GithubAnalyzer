"""Integration test configuration."""

import pytest
from GithubAnalyzer.analysis.services.parsers import TreeSitterParser

@pytest.fixture(scope="session")
def integration_parser():
    """Create parser for integration tests."""
    parser = TreeSitterParser()
    parser.initialize(["python", "javascript", "typescript", "tsx"])
    yield parser
    parser.cleanup() 