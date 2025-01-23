"""Tests for error handling utilities."""

import logging
import pytest
from typing import Optional

from src.GithubAnalyzer.core.utils.error_handler import handle_errors
from src.GithubAnalyzer.core.models.errors import ParserError, FileOperationError

@pytest.fixture
def error_logger(caplog):
    """Create a logger for testing."""
    caplog.set_level(logging.DEBUG)
    return logging.getLogger("test_error_handler")

def test_handle_errors_no_error():
    """Test handle_errors decorator with successful function."""
    @handle_errors()
    def successful_function():
        return "success"
    
    result = successful_function()
    assert result == "success"

def test_handle_errors_with_error(error_logger):
    """Test handle_errors decorator with error."""
    test_message = "Test error message"
    
    @handle_errors(message=test_message)
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        failing_function()
    
    assert test_message in error_logger.handlers[0].formatter.format(error_logger.handlers[0].records[0])

def test_handle_errors_specific_error():
    """Test handle_errors decorator with specific error type."""
    @handle_errors(error_type=ValueError)
    def failing_function():
        raise ValueError("Expected error")
    
    with pytest.raises(ValueError):
        failing_function()
    
    # Different error type should not be caught
    @handle_errors(error_type=ValueError)
    def different_error():
        raise TypeError("Unexpected error")
    
    with pytest.raises(TypeError):
        different_error()

def test_handle_errors_no_reraise(error_logger):
    """Test handle_errors decorator without reraising."""
    @handle_errors(reraise=False)
    def failing_function():
        raise ValueError("Test error")
    
    result = failing_function()
    assert result is None
    assert "Test error" in error_logger.handlers[0].formatter.format(error_logger.handlers[0].records[0])

def test_handle_errors_custom_log_level(error_logger):
    """Test handle_errors decorator with custom log level."""
    @handle_errors(log_level=logging.WARNING)
    def failing_function():
        raise ValueError("Test warning")
    
    with pytest.raises(ValueError):
        failing_function()
    
    record = error_logger.handlers[0].records[0]
    assert record.levelno == logging.WARNING

def test_handle_errors_with_parser_error(error_logger):
    """Test handle_errors decorator with ParserError."""
    @handle_errors(error_type=ParserError)
    def failing_function():
        raise ParserError("Failed to parse")
    
    with pytest.raises(ParserError):
        failing_function()
    
    assert "Failed to parse" in error_logger.handlers[0].formatter.format(error_logger.handlers[0].records[0])

def test_handle_errors_with_file_operation_error(error_logger):
    """Test handle_errors decorator with FileOperationError."""
    @handle_errors(error_type=FileOperationError)
    def failing_function():
        raise FileOperationError("File operation failed")
    
    with pytest.raises(FileOperationError):
        failing_function()
    
    assert "File operation failed" in error_logger.handlers[0].formatter.format(error_logger.handlers[0].records[0])

def test_handle_errors_with_args():
    """Test handle_errors decorator with function arguments."""
    @handle_errors()
    def function_with_args(x: int, y: Optional[str] = None):
        if y is None:
            raise ValueError(f"y is required when x is {x}")
        return f"{x}-{y}"
    
    # Test successful case
    result = function_with_args(1, "test")
    assert result == "1-test"
    
    # Test error case
    with pytest.raises(ValueError):
        function_with_args(1)

def test_handle_errors_nested():
    """Test nested handle_errors decorators."""
    @handle_errors(error_type=ValueError)
    @handle_errors(error_type=TypeError)
    def nested_function(x):
        if not isinstance(x, int):
            raise TypeError("Must be int")
        if x < 0:
            raise ValueError("Must be positive")
        return x
    
    # Test success
    assert nested_function(1) == 1
    
    # Test TypeError
    with pytest.raises(TypeError):
        nested_function("not int")
    
    # Test ValueError
    with pytest.raises(ValueError):
        nested_function(-1) 