"""Logging utilities for GithubAnalyzer."""
import sys
import json
import uuid
import time
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    import logging

# Standard logging levels
CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
NOTSET = 0

# Default settings
DEFAULT_LEVEL = INFO
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_INDENT = 2

import logging

# Get the project root directory (where src is)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

class StructuredFormatter:
    """Format log records as structured JSON with context."""
    
    def __init__(self, indent: Optional[int] = None):
        """Initialize formatter."""
        self.indent = indent
        
    def format(self, record: 'logging.LogRecord') -> str:
        """Format a log record as JSON with context."""
        # Get basic message
        message = record.msg
        if isinstance(message, dict):
            data = message
        else:
            data = {"message": str(message)}
            
        # Add standard fields
        data.update({
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name
        })
        
        # Add context if available
        if hasattr(record, "context"):
            data["context"] = record.context
            
        # Add exception info if present
        if record.exc_info:
            data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
            
        return json.dumps(data, indent=self.indent)
        
    def formatException(self, exc_info) -> str:
        """Format an exception info tuple."""
        import traceback
        return ''.join(traceback.format_exception(*exc_info))

class LoggerFactory:
    """Factory for creating and configuring loggers."""

    _instance = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern to ensure consistent logger configuration."""
        if cls._instance is None:
            cls._instance = super(LoggerFactory, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the factory if not already initialized."""
        if not self._initialized:
            self._formatter = StructuredFormatter()
            self._correlation_id = None
            self._initialized = True

    def _configure_logger(self, logger: 'logging.Logger', correlation_id: Optional[str] = None) -> None:
        """Configure a logger with common settings."""
        # Set correlation ID
        if correlation_id:
            self._correlation_id = correlation_id
        elif not self._correlation_id:
            self._correlation_id = str(uuid.uuid4())
            
        # Add correlation ID to logger
        logger.correlation_id = self._correlation_id
        logger.start_time = time.time()

        # Add file handler for persistent logging
        file_handler = logging.FileHandler(
            LOG_DIR / f"{logger.name.replace('.', '_')}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(self._formatter)
        logger.addHandler(file_handler)

    def get_logger(
        self,
        name: str,
        level: Optional[int] = None,
        correlation_id: Optional[str] = None
    ) -> 'logging.Logger':
        """Get a logger with consistent configuration."""
        logger = logging.getLogger(name)
        if level is not None:
            logger.setLevel(level)

        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Add console handler with structured formatting
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._formatter)
        logger.addHandler(console_handler)

        # Configure common settings
        self._configure_logger(logger, correlation_id)

        return logger

    def get_tree_sitter_logger(
        self,
        name: str = "tree_sitter",
        level: Optional[int] = None
    ) -> 'logging.Logger':
        """Get a tree-sitter specific logger.
        
        This creates a logger hierarchy:
        1. tree_sitter - Main logger for all tree-sitter operations
        2. tree_sitter.parser - For Parser.parse() callback logging
        3. tree_sitter.query - For Query operations
        
        Args:
            name: Base name for the logger (default: "tree_sitter")
            level: Logging level (default: DEBUG)
            
        Returns:
            The main tree-sitter logger
        """
        if level is None:
            level = DEBUG
            
        # Create main logger
        main_logger = logging.getLogger(name)
        main_logger.setLevel(level)
        
        # Create parser logger as child of main logger
        parser_logger = main_logger.getChild("parser")
        parser_logger.setLevel(level)
        parser_logger.propagate = True  # Ensure logs propagate to parent
        
        # Create query logger as child of main logger
        query_logger = main_logger.getChild("query")
        query_logger.setLevel(level)
        query_logger.propagate = True  # Ensure logs propagate to parent
        
        # Remove any existing handlers from all loggers
        for logger in [main_logger, parser_logger, query_logger]:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
        
        # Add console handler with structured formatting to main logger
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._formatter)
        console_handler.setLevel(level)
        main_logger.addHandler(console_handler)
        
        # Configure common settings but skip file handlers for test loggers
        if not name.startswith('test'):
            for logger in [main_logger, parser_logger, query_logger]:
                self._configure_logger(logger)
        
        return main_logger

# Create singleton instance
_factory = LoggerFactory()

def get_logger(name: str, level: Optional[int] = None, correlation_id: Optional[str] = None) -> 'logging.Logger':
    """Get a logger with consistent configuration."""
    return _factory.get_logger(name, level, correlation_id)

def get_tree_sitter_logger(name: str = "tree_sitter", level: Optional[int] = None) -> 'logging.Logger':
    """Get a tree-sitter specific logger.
    
    This creates a hierarchy of loggers:
    - {name} - Main tree-sitter logger
    - {name}.parser - For Parser.parse() callback logging
    - {name}.query - For Query operations
    
    Args:
        name: Base name for the logger (default: "tree_sitter")
        level: Logging level (default: DEBUG)
        
    Returns:
        The main tree-sitter logger
    """
    return _factory.get_tree_sitter_logger(name, level)

# Initialize logging with basic configuration
logging.basicConfig(
    level=DEFAULT_LEVEL,
    format=DEFAULT_FORMAT,
    stream=sys.stdout
)

__all__ = [
    'get_logger',
    'get_tree_sitter_logger',
    'StructuredFormatter',
    'LoggerFactory'
] 