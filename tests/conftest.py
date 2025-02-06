import pytest
from tree_sitter_language_pack import get_binding, get_language, get_parser

"""Test configuration and fixtures."""
from pathlib import Path

from tree_sitter import Language, Parser

from GithubAnalyzer.services.analysis.parsers.language_service import \
    LanguageService


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
def python_parser():
    """Create a Python parser."""
    return get_parser("python")

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
    import logging

    from GithubAnalyzer.utils.logging import (LoggerFactory,
                                              StructuredFormatter, get_logger)

    # Create logger factory instance
    factory = LoggerFactory()
    
    # Configure main logger with structured formatting
    main_logger = factory.get_logger('test', level=logging.DEBUG)
    
    # Set up tree-sitter specific logging with structured formatting
    ts_logger = factory.get_logger('tree_sitter', level=logging.DEBUG)
    
    # Add console handler with structured formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    ts_logger.addHandler(console_handler)
    
    # Suppress service unavailable warnings
    service_logger = factory.get_logger('services')
    service_logger.setLevel(logging.ERROR)  # Only show errors, not warnings
    
    # Suppress Neo4j connection warnings
    neo4j_logger = factory.get_logger('neo4j')
    neo4j_logger.setLevel(logging.ERROR)
    
    # Suppress database warnings
    db_logger = factory.get_logger('database')
    db_logger.setLevel(logging.ERROR)
    
    return {
        'main_logger': main_logger,
        'ts_logger': ts_logger,
        'parser_logger': ts_logger.getChild('parser'),
        'service_logger': service_logger,
        'neo4j_logger': neo4j_logger,
        'db_logger': db_logger
    }

@pytest.fixture
def python_parser_with_logging(test_logging_setup):
    """Create a Python parser with logging enabled."""
    # Just return the parser since tree-sitter-language-pack parsers don't support direct logger setting
    return get_parser("python")