"""Security test configuration."""

import pytest
from GithubAnalyzer.services.core.parsers import TreeSitterParser

@pytest.fixture(scope="session")
def security_parser():
    """Create parser for security tests."""
    parser = TreeSitterParser()
    parser.initialize()
    yield parser
    parser.cleanup() 