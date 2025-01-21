"""Test tree-sitter parser implementation."""
import pytest
from pathlib import Path

from src.GithubAnalyzer.analysis.services.parsers.tree_sitter import (
    TreeSitterParser,
    QUERY_TIMEOUT_MS,
    MAX_RECOVERY_ATTEMPTS
)
from src.GithubAnalyzer.core.services.file_service import FileService
from src.GithubAnalyzer.common.services.cache_service import CacheService
from src.GithubAnalyzer.core.utils.context_manager import ContextManager
from src.GithubAnalyzer.core.models.errors import ParserError

@pytest.fixture
def parser():
    """Create a basic tree-sitter parser."""
    return TreeSitterParser()

@pytest.fixture
def full_parser():
    """Create a fully configured tree-sitter parser."""
    cache_service = CacheService()
    file_service = FileService()
    context_manager = ContextManager()
    return TreeSitterParser(
        cache_service=cache_service,
        file_service=file_service,
        context_manager=context_manager
    )

def test_parser_initialization(parser):
    """Test basic parser initialization."""
    # Check default languages
    assert "python" in parser.languages
    assert "javascript" in parser.languages
    assert "typescript" in parser.languages
    
    # Check parser configuration
    assert parser.parsers["python"].timeout_micros == QUERY_TIMEOUT_MS * 1000

def test_parser_cleanup(parser):
    """Test parser cleanup."""
    parser.cleanup()
    assert len(parser.languages) == 0
    assert len(parser.parsers) == 0

def test_parse_valid_python(parser):
    """Test parsing valid Python code."""
    code = "def test(): return 42"
    result = parser.parse(code, "python")
    assert result.is_valid
    assert result.tree is not None
    assert result.errors == []

def test_parse_invalid_python(parser):
    """Test parsing invalid Python code."""
    code = "def test() return 42"  # Missing colon
    result = parser.parse(code, "python")
    assert not result.is_valid
    assert len(result.errors) > 0

def test_parse_with_recovery(parser):
    """Test error recovery during parsing."""
    code = """
    def test()  # Missing colon
        print("Hello")
        return 42
    """
    result = parser.parse(code, "python", recovery_enabled=True)
    assert not result.is_valid
    assert result.recovery_attempts > 0

def test_parse_file(full_parser, tmp_path):
    """Test file parsing."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("def test(): pass")
    
    result = full_parser.parse_file(test_file)
    assert result.is_valid
    assert result.tree is not None

def test_language_detection(parser):
    """Test language detection from file extensions."""
    assert parser._detect_language(Path("test.py")) == "python"
    assert parser._detect_language(Path("test.js")) == "javascript"
    assert parser._detect_language(Path("test.ts")) == "typescript"
    assert parser._detect_language(Path("test.unknown")) is None

def test_unsupported_language(parser):
    """Test handling of unsupported languages."""
    with pytest.raises(ValueError):
        parser.parse("code", "unsupported")

def test_parse_empty_file(full_parser, tmp_path):
    """Test parsing empty file."""
    empty_file = tmp_path / "empty.py"
    empty_file.write_text("")
    
    result = full_parser.parse_file(empty_file)
    assert result.is_valid  # Empty file is valid syntax
    assert result.node_count == 1  # Just root node

def test_parse_with_cache(full_parser, tmp_path):
    """Test parsing with cache."""
    test_file = tmp_path / "cached.py"
    test_file.write_text("def test(): pass")
    
    # First parse should cache
    result1 = full_parser.parse_file(test_file)
    # Second parse should use cache
    result2 = full_parser.parse_file(test_file)
    
    assert result1.tree is not None
    assert result2.tree is not None 