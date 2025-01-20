"""Tests for verifying proper initialization of the parser service component."""

import pytest
from pathlib import Path
from typing import Generator, List, Optional

from tree_sitter import Language, Parser, Query

from GithubAnalyzer import TreeSitterParser
from GithubAnalyzer.core.models.errors import ParserError, FileOperationError
from GithubAnalyzer.core.models.file import FileInfo, FileType, FileFilterConfig
from GithubAnalyzer.core.services.file_service import FileService
from GithubAnalyzer.common.services.cache_service import CacheService

@pytest.fixture
def cache_service() -> Generator[CacheService, None, None]:
    """Create a cache service."""
    service = CacheService(max_size=100)
    service.initialize()
    yield service
    service.cleanup()

@pytest.fixture
def file_service() -> Generator[FileService, None, None]:
    """Create a file service."""
    service = FileService(filter_config=FileFilterConfig(
        include_patterns=[],
        exclude_patterns=[],
        max_size=1024 * 1024,  # 1MB
        allowed_types=None
    ))
    service.initialize()
    yield service
    service.cleanup()

@pytest.fixture
def parser(file_service: FileService, cache_service: CacheService) -> Generator[TreeSitterParser, None, None]:
    """Create a TreeSitterParser instance."""
    parser = TreeSitterParser(file_service=file_service, cache_service=cache_service)
    yield parser
    parser.cleanup()

@pytest.fixture
def test_files(tmp_path: Path) -> Generator[Path, None, None]:
    """Create test files with various docstring/comment patterns."""
    # Python file with docstrings and comments
    python_file = tmp_path / "test.py"
    python_file.write_text('''
# Regular comment
"""Module docstring."""

def test():
    """Function docstring."""
    # Function comment
    return True

class TestClass:
    """Class docstring."""
    # Class comment
    
    def method(self):
        """Method docstring."""
        # Method comment
        pass
''')
    
    yield tmp_path

def test_basic_initialization(parser: TreeSitterParser) -> None:
    """Test basic parser initialization."""
    parser.initialize(["python"])
    assert parser.initialized
    assert "python" in parser.supported_languages

def test_language_query_support(parser: TreeSitterParser) -> None:
    """Test that initialized languages support querying."""
    parser.initialize(["python"])
    binding = parser._language_bindings["python"]
    
    # Test query compilation
    doc_str_pattern = '''
        (module . (comment)* . (expression_statement (string)) @module_doc_str)
        (class_definition
            body: (block . (expression_statement (string)) @class_doc_str))
        (function_definition
            body: (block . (expression_statement (string)) @function_doc_str))
    '''
    query = binding.language.query(doc_str_pattern)
    assert isinstance(query, Query)

def test_parser_with_docstrings(parser: TreeSitterParser, test_files: Path, file_service: FileService) -> None:
    """Test parsing file with docstrings and comments."""
    parser.initialize(["python"])
    file_info = file_service.get_file_info(test_files / "test.py")
    
    result = parser.parse_file(file_info)
    assert result.success
    assert result.ast is not None
    
    # Get docstrings using query
    binding = parser._language_bindings["python"]
    doc_str_pattern = '''
        (module . (comment)* . (expression_statement (string)) @module_doc_str)
        (class_definition
            body: (block . (expression_statement (string)) @class_doc_str))
        (function_definition
            body: (block . (expression_statement (string)) @function_doc_str))
    '''
    query = binding.language.query(doc_str_pattern)
    captures = query.captures(result.ast.root_node)
    
    # Extract docstrings from captures dictionary
    doc_strings = []
    for capture_name, nodes in captures.items():
        doc_strings.extend(node.text.decode() for node in nodes)
        
    assert '"""Module docstring."""' in doc_strings
    assert '"""Function docstring."""' in doc_strings
    assert '"""Class docstring."""' in doc_strings
    assert '"""Method docstring."""' in doc_strings

def test_comment_detection(parser: TreeSitterParser, test_files: Path, file_service: FileService) -> None:
    """Test detection of regular comments."""
    parser.initialize(["python"])
    file_info = file_service.get_file_info(test_files / "test.py")
    
    result = parser.parse_file(file_info)
    assert result.success
    
    # Get comments using query
    binding = parser._language_bindings["python"]
    comment_pattern = '(comment) @comment'
    query = binding.language.query(comment_pattern)
    captures = query.captures(result.ast.root_node)
    
    # Extract comments from captures dictionary
    comments = []
    for nodes in captures.values():
        comments.extend(node.text.decode() for node in nodes)
        
    assert "# Regular comment" in comments
    assert "# Function comment" in comments
    assert "# Class comment" in comments
    assert "# Method comment" in comments

def test_cleanup(parser: TreeSitterParser) -> None:
    """Test parser cleanup."""
    parser.initialize(["python"])
    assert parser.initialized
    
    parser.cleanup()
    assert not parser.initialized
    assert not parser._language_bindings

def test_initialization_errors(parser: TreeSitterParser) -> None:
    """Test handling of initialization errors."""
    with pytest.raises(ParserError, match="Language not found"):
        parser.initialize(["nonexistent_language"])
        
    # Test partial initialization with some invalid languages
    parser.initialize(["python", "nonexistent_language", "javascript"])
    assert "python" in parser.supported_languages
    assert "javascript" in parser.supported_languages
    assert "nonexistent_language" not in parser.supported_languages
