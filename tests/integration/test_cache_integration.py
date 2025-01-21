"""Test cache integration with services."""
import pytest

def test_cache_service_integration(cache_service, file_service):
    """Test cache service works with file and parser services."""
    from src.GithubAnalyzer.core.services.parser_service import ParserService
    from src.GithubAnalyzer.analysis.services.parser_registry import ParserRegistry
    
    # Setup services
    parser_service = ParserService(cache_service)
    parser_service.initialize()
    
    # Register parsers through registry
    registry = ParserRegistry(parser_service=parser_service, cache_service=cache_service)
    registry.register_parsers()
    
    # Now we can parse content
    result1 = parser_service.parse_content("def test(): pass", "python")
    result2 = parser_service.parse_content("def test(): pass", "python")
    
    assert result1.cache_key == result2.cache_key
    assert cache_service.get("ast", result1.cache_key) is not None 