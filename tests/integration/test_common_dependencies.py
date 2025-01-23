"""Test common dependencies."""
from logging import Logger
from src.GithubAnalyzer.core.utils.logging import get_logger

def test_logger_initialization():
    """Test logger initialization."""
    logger = get_logger(__name__)
    assert isinstance(logger, Logger), "Logger should be instance of Logger" 