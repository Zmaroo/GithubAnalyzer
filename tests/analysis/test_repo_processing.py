"""Test suite for repository processing flow."""
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, Any
import pytest
from unittest.mock import patch, MagicMock

from tree_sitter import Parser, Language, Tree
from GithubAnalyzer.services.core.repo_processor import RepoProcessor
from GithubAnalyzer.services.core.file_service import FileService
from GithubAnalyzer.services.analysis.parsers.language_service import LanguageService
from GithubAnalyzer.services.analysis.parsers.query_service import TreeSitterQueryHandler
from GithubAnalyzer.services.analysis.parsers.custom_parsers import get_custom_parser
from GithubAnalyzer.utils.logging import get_logger, LoggerFactory
from GithubAnalyzer.utils.logging.tree_sitter_logging import TreeSitterLogHandler

# Set up logging for tests
logger = get_logger(__name__)

@pytest.fixture
def setup_test_logging(test_logging_setup):
    """Set up test logging with tree-sitter integration."""
    return test_logging_setup

@pytest.fixture
def sample_repo():
    """Create a temporary repository with sample files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir)
        
        # Create Python file
        with open(repo_dir / "main.py", "w") as f:
            f.write('''
def hello():
    print("Hello, World!")
            
class TestClass:
    def test_method(self):
        hello()
''')
        
        # Create config files
        with open(repo_dir / ".env", "w") as f:
            f.write('''
DB_HOST=localhost
DB_PORT=5432
''')
        
        with open(repo_dir / "requirements.txt", "w") as f:
            f.write('''
pytest>=7.0.0
tree-sitter==0.24.0
''')
        
        # Create JSON file
        with open(repo_dir / "config.json", "w") as f:
            f.write('''
{
    "name": "test",
    "version": "1.0.0"
}
''')
        
        yield repo_dir

def test_repo_processing_flow(sample_repo, setup_test_logging, python_parser_with_logging):
    """Test the complete repository processing flow."""
    loggers = setup_test_logging
    repo_processor = RepoProcessor()
    
    # 1. Test language detection
    file_service = FileService()
    python_file = sample_repo / "main.py"
    env_file = sample_repo / ".env"
    
    # Check Python file detection
    python_info = file_service._detect_language(python_file)
    assert python_info == "python"
    loggers['main_logger'].info(f"Detected language for {python_file}: {python_info}")
    
    # Check .env file detection
    env_info = file_service._detect_language(env_file)
    assert env_info == "env"
    loggers['main_logger'].info(f"Detected language for {env_file}: {env_info}")
    
    # 2. Test custom parser integration
    with open(env_file) as f:
        env_content = f.read()
    env_parser = get_custom_parser(str(env_file))
    env_ast = env_parser.parse(env_content)
    assert env_ast is not None
    assert "DB_HOST" in env_ast
    loggers['main_logger'].info(f"Custom parser AST for {env_file}: {env_ast}")
    
    # 3. Test tree-sitter parsing with v24 logging
    with open(python_file) as f:
        content = f.read()
    tree = python_parser_with_logging.parse(bytes(content, "utf8"))
    assert tree is not None
    assert not tree.root_node.has_error
    
    # Verify parser logged information
    parser_logs = loggers['ts_handler'].parse_records
    assert len(parser_logs) > 0
    loggers['main_logger'].info(f"Tree-sitter parse logs: {len(parser_logs)} records")
    
    # 4. Test query handling
    query_handler = TreeSitterQueryHandler(language=tree.language, language_name="python")
    
    # Find functions using tree-sitter query
    functions = query_handler.find_functions(tree.root_node)
    assert len(functions) == 2  # hello() and test_method()
    loggers['main_logger'].info(f"Found functions: {[f['name'].text.decode() for f in functions]}")
    
    # 5. Test complete repo processing
    files = file_service.get_repository_files(sample_repo)
    assert len(files) > 0
    
    # Process each file
    for file_info in files:
        result = repo_processor.process_file(file_info)
        assert result is not None
        loggers['main_logger'].info(f"Processed {file_info.path}: {result.language}")

def test_tree_sitter_logging(setup_test_logging, python_parser_with_logging):
    """Test tree-sitter v24 logging integration."""
    loggers = setup_test_logging
    ts_handler = loggers['ts_handler']
    
    # Clear any existing logs
    ts_handler.clear()
    
    # Parse some code with potential issues to generate logs
    code = """
    def broken_function(
        print("Missing closing parenthesis"
    """
    
    tree = python_parser_with_logging.parse(bytes(code, "utf8"))
    assert tree.root_node.has_error
    
    # Verify parser logged the syntax error
    assert len(ts_handler.error_records) > 0, "No error records found"
    assert len(ts_handler.parse_records) > 0, "No parse records found"
    
    # Check error log content
    for log in ts_handler.error_records:
        assert any(err in log.msg.lower() for err in ['syntax error', 'parse error', 'missing'])
        loggers['main_logger'].info(f"Tree-sitter error log: {log.msg}")
    
    # Check parse log content
    for log in ts_handler.parse_records:
        assert hasattr(log, 'msecs'), "Log record missing timing information"
        assert hasattr(log, 'thread'), "Log record missing thread information"
        loggers['main_logger'].info(f"Tree-sitter parse log: {log.msg}")

def test_query_optimization_logging(setup_test_logging, python_parser_with_logging):
    """Test query optimization logging."""
    loggers = setup_test_logging
    ts_handler = loggers['ts_handler']
    
    # Clear any existing logs
    ts_handler.clear()
    
    # Create query handler with logging
    query_handler = TreeSitterQueryHandler()
    
    # Create a complex query that can be optimized
    query_str = """
    (function_definition
        name: (identifier) @function.name
        parameters: (parameters) @function.params
        body: (block) @function.body)
    """
    
    # Create and execute query
    query = query_handler.create_query(query_str, "python")
    
    # Verify query logs
    assert len(ts_handler.query_records) > 0, "No query records found"
    
    # Check query log content
    for log in ts_handler.query_records:
        assert hasattr(log, 'msecs'), "Log record missing timing information"
        assert hasattr(log, 'thread'), "Log record missing thread information"
        loggers['main_logger'].info(f"Query optimization log: {log.msg}") 