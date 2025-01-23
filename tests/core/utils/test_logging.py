"""Tests for logging utilities."""

import logging
import pytest
from typing import Dict, Any

from src.GithubAnalyzer.core.utils.logging import (
    configure_logging,
    get_logger,
    log_exceptions,
    StructuredLogger
)

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Create a test logging configuration."""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'default': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout'
            }
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }

def test_configure_logging_with_config(test_config, caplog):
    """Test configuring logging with custom config."""
    configure_logging(test_config)
    logger = logging.getLogger()
    logger.info("Test message")
    assert "INFO - Test message" in caplog.text

def test_configure_logging_with_env(caplog):
    """Test configuring logging with environment."""
    configure_logging(env="test")
    logger = logging.getLogger()
    logger.info("Test message")
    assert "Test message" in caplog.text

def test_get_logger():
    """Test getting a logger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"

def test_log_exceptions_with_logger(caplog):
    """Test log_exceptions decorator with provided logger."""
    test_logger = logging.getLogger("test")
    
    @log_exceptions(test_logger)
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        failing_function()
    
    assert "Exception in failing_function: Test error" in caplog.text

def test_log_exceptions_without_logger(caplog):
    """Test log_exceptions decorator without logger."""
    @log_exceptions()
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        failing_function()
    
    assert "Exception in failing_function: Test error" in caplog.text

def test_log_exceptions_success():
    """Test log_exceptions decorator with successful function."""
    @log_exceptions()
    def successful_function():
        return "success"
    
    result = successful_function()
    assert result == "success"

class TestStructuredLogger:
    """Tests for StructuredLogger class."""
    
    @pytest.fixture
    def structured_logger(self):
        """Create a StructuredLogger instance."""
        return StructuredLogger("test_structured")
    
    def test_init(self, structured_logger):
        """Test logger initialization."""
        assert structured_logger._logger.name == "test_structured"
        assert structured_logger._context == {}
    
    def test_add_context(self, structured_logger):
        """Test adding context."""
        structured_logger.add_context(user="test", action="login")
        assert structured_logger._context == {"user": "test", "action": "login"}
        
        # Add more context
        structured_logger.add_context(status="success")
        assert structured_logger._context == {
            "user": "test",
            "action": "login",
            "status": "success"
        }
    
    def test_clear_context(self, structured_logger):
        """Test clearing context."""
        structured_logger.add_context(user="test")
        structured_logger.clear_context()
        assert structured_logger._context == {}
    
    def test_format_message_with_context(self, structured_logger):
        """Test message formatting with context."""
        structured_logger.add_context(user="test")
        msg = structured_logger._format_message("Hello")
        assert msg == "Hello [user=test]"
    
    def test_format_message_without_context(self, structured_logger):
        """Test message formatting without context."""
        msg = structured_logger._format_message("Hello")
        assert msg == "Hello"
    
    def test_logging_methods(self, structured_logger, caplog):
        """Test all logging methods."""
        structured_logger.add_context(user="test")
        
        # Test each logging method
        structured_logger.debug("Debug message", extra="debug")
        structured_logger.info("Info message", extra="info")
        structured_logger.warning("Warning message", extra="warn")
        structured_logger.error("Error message", extra="error")
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            structured_logger.exception("Exception message", extra="exc")
        
        # Verify log messages
        assert "Debug message [user=test]" in caplog.text
        assert "Info message [user=test]" in caplog.text
        assert "Warning message [user=test]" in caplog.text
        assert "Error message [user=test]" in caplog.text
        assert "Exception message [user=test]" in caplog.text
        assert "ValueError: Test exception" in caplog.text
    
    def test_logging_with_extra_context(self, structured_logger, caplog):
        """Test logging with additional context."""
        structured_logger.add_context(user="test")
        structured_logger.info("Message", action="test")
        assert "Message [user=test]" in caplog.text
        assert "action=test" in caplog.text 