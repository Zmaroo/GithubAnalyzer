"""Logging configuration for GithubAnalyzer."""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from tree_sitter import Parser

from . import get_logger, get_tree_sitter_logger

def configure_test_logging() -> Dict[str, Any]:
    """Configure logging for tests.
    
    Returns:
        Dictionary containing configured loggers and handlers
    """
    # Create main test logger
    main_logger = get_logger('test')
    
    # Create tree-sitter logger hierarchy
    ts_logger = get_tree_sitter_logger('tree_sitter')
    
    # Set debug level for all loggers
    main_logger.setLevel(logging.DEBUG)
    ts_logger.setLevel(logging.DEBUG)
    
    # Return dict of loggers for test verification
    return {
        'main_logger': main_logger,
        'ts_logger': ts_logger,
        'parser_logger': ts_logger.getChild('parser'),
        'query_logger': ts_logger.getChild('query')
    }

def configure_parser_logging(parser: Parser, logger_name: str = "tree_sitter") -> 'logging.Logger':
    """Configure logging for a tree-sitter parser.
    
    Args:
        parser: The parser to configure logging for
        logger_name: Base name for the logger
        
    Returns:
        The configured logger
    """
    # Get the tree-sitter logger
    ts_logger = get_tree_sitter_logger(logger_name)
    
    # Create a logging callback
    def logger_callback(msg: str) -> None:
        ts_logger.debug(msg, extra={'context': {'source': 'tree-sitter', 'type': 'parser'}})
    
    # Set the logger on the parser
    parser.logger = logger_callback
    
    return ts_logger 