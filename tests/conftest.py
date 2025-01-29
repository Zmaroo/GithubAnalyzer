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
    return Path(__file__).parent / "data"

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
    parser.set_language(python_language)
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
    """Set up test logging with tree-sitter v24 integration."""
    from GithubAnalyzer.utils.logging import get_logger, get_tree_sitter_logger
    from GithubAnalyzer.utils.logging.tree_sitter_logging import TreeSitterLogHandler
    import logging
    
    # Create loggers
    main_logger = get_logger('test')
    ts_logger = get_tree_sitter_logger('tree_sitter')
    parser_logger = get_logger('tree_sitter.parser')
    
    # Configure handler
    ts_handler = TreeSitterLogHandler('tree_sitter')
    ts_handler.setLevel(logging.DEBUG)
    
    # Add handler to all loggers
    main_logger.addHandler(ts_handler)
    ts_logger.addHandler(ts_handler)
    parser_logger.addHandler(ts_handler)
    
    # Set debug level for all loggers
    main_logger.setLevel(logging.DEBUG)
    ts_logger.setLevel(logging.DEBUG)
    parser_logger.setLevel(logging.DEBUG)
    
    return {
        'main_logger': main_logger,
        'ts_logger': ts_logger,
        'parser_logger': parser_logger,
        'ts_handler': ts_handler
    }

@pytest.fixture
def python_parser_with_logging(python_parser, test_logging_setup):
    """Create a Python parser with tree-sitter v24 logging enabled."""
    ts_handler = test_logging_setup['ts_handler']
    ts_handler.enable_parser_logging(python_parser)
    return python_parser 