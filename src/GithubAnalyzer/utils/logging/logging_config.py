"""Logging configuration for GithubAnalyzer."""

import logging
import sys
import json
from typing import Optional, Dict, Any

class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""
    
    def __init__(self, indent: Optional[int] = None):
        """Initialize formatter.
        
        Args:
            indent: Optional JSON indentation level
        """
        super().__init__()
        self.indent = indent
        
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON."""
        if isinstance(record.msg, dict):
            message = record.msg.get("message", str(record.msg))
            context = record.msg.get("context", {})
        else:
            message = str(record.msg)
            context = {}
            
        output = {
            "message": message,
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name
        }
        
        if context:
            # Pretty format nested dictionaries
            if isinstance(context, dict):
                for key, value in context.items():
                    if isinstance(value, dict):
                        context[key] = json.dumps(value, indent=2)
            output["context"] = context
            
        return json.dumps(output, indent=self.indent)

def configure_logging(
    level: int = logging.INFO,
    structured: bool = True,
    enable_tree_sitter: bool = False,
    log_file: Optional[str] = None,
    indent: Optional[int] = 2
) -> None:
    """Configure logging for the application.
    
    Args:
        level: Logging level
        structured: Whether to use structured JSON logging
        enable_tree_sitter: Whether to enable tree-sitter specific logging
        log_file: Optional file to write logs to
        indent: JSON indentation level for structured logging
    """
    # Remove any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = JsonFormatter(indent=indent) if structured else logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set level
    root_logger.setLevel(level)
    
    # Configure tree-sitter logging if enabled
    if enable_tree_sitter:
        ts_logger = logging.getLogger('tree_sitter')
        ts_logger.setLevel(level)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name) 