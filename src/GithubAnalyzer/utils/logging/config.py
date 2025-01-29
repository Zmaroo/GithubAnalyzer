"""Logging configuration for GithubAnalyzer."""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from tree_sitter import Parser

from .tree_sitter_logging import TreeSitterLogHandler
from . import get_logger, get_tree_sitter_logger

def configure_test_logging() -> Dict[str, Any]:
    """Configure logging for tests.
    
    Returns:
        Dictionary containing configured loggers and handlers
    """
    # Create main test logger
    main_logger = get_logger('test')
    
    # Create tree-sitter logger hierarchy with a new handler
    ts_logger = get_tree_sitter_logger('tree_sitter')
    
    # Create a new handler specifically for tests
    ts_handler = TreeSitterLogHandler('tree_sitter')
    ts_handler.setLevel(logging.DEBUG)
    
    # Add handler to all loggers in the hierarchy
    ts_logger.addHandler(ts_handler)
    ts_logger.getChild('parser').addHandler(ts_handler)
    ts_logger.getChild('query').addHandler(ts_handler)
    
    # Set debug level for all loggers
    main_logger.setLevel(logging.DEBUG)
    ts_logger.setLevel(logging.DEBUG)
    
    # Return dict of loggers and handler for test verification
    return {
        'main_logger': main_logger,
        'ts_logger': ts_logger,
        'ts_handler': ts_handler,
        'parser_logger': ts_logger.getChild('parser'),
        'query_logger': ts_logger.getChild('query')
    }

def configure_parser_logging(parser: Parser, logger_name: str = "tree_sitter") -> TreeSitterLogHandler:
    """Configure logging for a tree-sitter parser.
    
    Args:
        parser: The parser to configure logging for
        logger_name: Base name for the logger
        
    Returns:
        The configured TreeSitterLogHandler
    """
    # Create handler and get logger
    ts_handler = TreeSitterLogHandler(logger_name)
    ts_logger = get_tree_sitter_logger(logger_name)
    
    # Add handler to logger if not already present
    if ts_handler not in ts_logger.handlers:
        ts_logger.addHandler(ts_handler)
    
    # Enable logging on the handler
    ts_handler.enable()
    
    # Enable parser logging
    ts_handler.enable_parser_logging(parser)
    
    # Clear any existing logs
    ts_handler.clear()
    
    return ts_handler 