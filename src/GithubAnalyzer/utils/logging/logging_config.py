"""Logging configuration for GithubAnalyzer."""

import logging
import sys
from pathlib import Path
from typing import Optional, Union
from .formatters import StructuredFormatter
from .tree_sitter_logging import TreeSitterLogHandler

def configure_logging(
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    structured: bool = False,
    enable_tree_sitter: bool = False,
) -> None:
    """Configure logging for GithubAnalyzer.
    
    Args:
        level: The logging level to use. Defaults to INFO.
        log_file: Optional path to a log file. If provided, logs will be written to this file.
        structured: Whether to use structured logging format. Defaults to False.
        enable_tree_sitter: Whether to enable tree-sitter logging. Defaults to False.
    """
    # Remove any existing handlers to prevent duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set root logger level
    root_logger.setLevel(level)
    
    # Configure tree-sitter logger if enabled
    if enable_tree_sitter:
        tree_sitter_logger = logging.getLogger('tree-sitter')
        tree_sitter_logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers
        for handler in tree_sitter_logger.handlers[:]:
            tree_sitter_logger.removeHandler(handler)
            
        # Add TreeSitterLogHandler
        tree_sitter_handler = TreeSitterLogHandler()
        tree_sitter_handler.setFormatter(formatter)
        tree_sitter_logger.addHandler(tree_sitter_handler)
        
        # Log that tree-sitter logging is enabled
        tree_sitter_logger.debug({
            "message": "Tree-sitter logging enabled",
            "context": {
                "level": logging.getLevelName(level),
                "structured": structured,
                "log_file": str(log_file) if log_file else None
            }
        })

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.
    
    Args:
        name: The name of the logger.
        
    Returns:
        A logger instance.
    """
    return logging.getLogger(name) 