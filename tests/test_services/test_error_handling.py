"""Test error handling across services"""
import pytest
from GithubAnalyzer.core.models.errors import (
    AnalysisError,
    ParseError,
    DatabaseError
)
from GithubAnalyzer.core.error_handler import handle_errors

def test_error_handler_decorator():
    """Test error handler decorator"""
    
    @handle_errors(ParseError)
    def failing_function():
        raise ValueError("Test error")
        
    result = failing_function()
    assert isinstance(result, ParseError)
    assert "Test error" in result.message
    assert result.code == "ValueError"

def test_database_error_handling(registry):
    """Test database error handling"""
    # Force database error
    registry.database_service.connections['postgres'] = None
    
    result = registry.database_service.store_repository_info({})
    assert isinstance(result, DatabaseError)
    assert result.recoverable is False

def test_malformed_input_handling(registry):
    """Test handling of malformed input"""
    result = registry.analyzer_service.analyze_file("nonexistent/path")
    assert result is None
    
    result = registry.parser_service.parse_file("", "")
    assert not result.success
    assert "Empty content" in result.errors[0] 