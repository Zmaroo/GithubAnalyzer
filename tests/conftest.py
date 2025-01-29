from tree_sitter_language_pack import get_parser, get_binding, get_language
import pytest
"""Test configuration and fixtures."""
from pathlib import Path
from tree_sitter import Language, Parser

@pytest.fixture
def repo_url():
    """Get a test repository URL."""
    return "https://github.com/tree-sitter/tree-sitter-python"

@pytest.fixture
def test_data_dir():
    """Get the test data directory."""
    data_dir = Path(__file__).parent / "data"
    assert data_dir.exists(), "Test data directory not found"
    
    # Check that test files exist
    test_files = [
        "test.py",
        ".env",
        "requirements.txt",
        ".editorconfig",
        ".gitignore"
    ]
    
    for file in test_files:
        assert (data_dir / file).exists(), f"Test file {file} not found"
        
    return data_dir

@pytest.fixture
def python_binding():
    """Get Python language binding."""
    return get_binding("python")

@pytest.fixture
def python_language():
    """Get Python Language object."""
    return get_language("python")

@pytest.fixture
def python_parser(python_language):
    """Create a Python parser with proper language initialization."""
    parser = Parser()
    parser.language = python_language  # v24 API change
    return parser

@pytest.fixture
def simple_tree(python_parser):
    """Create a simple Python AST."""
    code = "def test(): pass"
    return python_parser.parse(bytes(code, "utf8"))

@pytest.fixture
def complex_tree(python_parser):
    """Create a more complex Python AST."""
    code = """
def hello(name):
    print(f"Hello {name}")
    return True

class Greeter:
    def __init__(self):
        pass
        
    def greet(self, name):
        print(f"Hi {name}")
"""
    return python_parser.parse(bytes(code, "utf8"))

@pytest.fixture
def test_logging_setup():
    """Set up logging for tests."""
    from GithubAnalyzer.utils.logging.config import configure_test_logging
    return configure_test_logging()

@pytest.fixture
def python_parser_with_logging(python_parser, test_logging_setup):
    """Create a Python parser with tree-sitter v24 logging enabled."""
    from GithubAnalyzer.utils.logging.config import configure_parser_logging
    configure_parser_logging(python_parser, "tree_sitter")
    return python_parser 