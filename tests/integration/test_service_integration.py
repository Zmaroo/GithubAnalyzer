"""Test integration between services."""
import pytest
from pathlib import Path

from src.GithubAnalyzer.common.services.cache_service import CacheService
from src.GithubAnalyzer.core.services.parser_service import ParserService
from src.GithubAnalyzer.core.services.file_service import FileService
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter import TreeSitterParser
from src.GithubAnalyzer.analysis.services.parser_registry import ParserRegistry

def test_end_to_end_parsing(tmp_path: Path):
    """Test complete parsing flow with all services."""
    # Setup services
    cache_service = CacheService()
    cache_service.initialize()
    
    file_service = FileService()
    file_service.initialize()
    
    parser_service = ParserService(cache_service)
    parser_service.initialize()
    
    # Register parsers through registry
    registry = ParserRegistry(parser_service=parser_service, cache_service=cache_service)
    registry.register_parsers()
    
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("""
def hello():
    '''Doc string'''
    print("Hello, World!")
    return 42
""")
    
    # Process file
    file_info = file_service.get_file_info(test_file)
    result = parser_service.parse_file(file_info)
    
    # Verify results
    assert result.is_valid
    assert result.tree is not None

def test_parser_registry_integration():
    """Test parser registry with multiple parser types."""
    from src.GithubAnalyzer.analysis.services.parser_registry import ParserRegistry
    from src.GithubAnalyzer.core.services.parser_service import ParserService
    from src.GithubAnalyzer.common.services.cache_service import CacheService

    # Setup services
    cache_service = CacheService()
    parser_service = ParserService(cache_service)
    parser_service.initialize()

    # Create and register parsers
    registry = ParserRegistry(parser_service=parser_service, cache_service=cache_service)
    registry.register_parsers()

    # Verify parsers are registered
    assert parser_service._parsers.get("tree-sitter") is not None
    assert parser_service._parsers.get("documentation") is not None
    assert parser_service._parsers.get("license") is not None 