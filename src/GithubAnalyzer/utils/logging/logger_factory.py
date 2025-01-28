"""Factory for creating and configuring loggers."""
from typing import Optional
import logging
import time
import uuid
from pathlib import Path
from .tree_sitter_logging import TreeSitterLogHandler
from .formatters import StructuredFormatter

class LoggerFactory:
    """Factory for creating and configuring loggers with consistent settings."""

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

    def _configure_logger(self, logger: logging.Logger, correlation_id: Optional[str] = None) -> None:
        """Configure a logger with common settings.
        
        Args:
            logger: Logger to configure
            correlation_id: Optional correlation ID
        """
        # Set correlation ID
        if correlation_id:
            self._correlation_id = correlation_id
        elif not self._correlation_id:
            self._correlation_id = str(uuid.uuid4())
            
        # Add correlation ID to logger
        logger.correlation_id = self._correlation_id
        logger.start_time = time.time()

        # Add file handler for persistent logging
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f"{logger.name.replace('.', '_')}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(self._formatter)
        logger.addHandler(file_handler)

    def get_logger(
        self,
        name: str,
        level: int = logging.DEBUG,
        correlation_id: Optional[str] = None
    ) -> logging.Logger:
        """Get a logger with consistent configuration.
        
        Args:
            name: Logger name
            level: Logging level
            correlation_id: Optional correlation ID for tracking operations
            
        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
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
        level: int = logging.DEBUG
    ) -> logging.Logger:
        """Get a tree-sitter specific logger.
        
        Args:
            name: Logger name (defaults to tree_sitter)
            level: Logging level
            
        Returns:
            Configured tree-sitter logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Add TreeSitterLogHandler
        ts_handler = TreeSitterLogHandler(name)
        ts_handler.setFormatter(self._formatter)
        logger.addHandler(ts_handler)

        # Configure common settings
        self._configure_logger(logger)

        return logger

    def update_correlation_id(self, correlation_id: str) -> None:
        """Update the correlation ID for tracking related operations.
        
        Args:
            correlation_id: New correlation ID to use
        """
        self._correlation_id = correlation_id 