"""Logging configuration for GithubAnalyzer."""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from tree_sitter import Parser, LogType

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
    
    # Create a logging callback that handles both PARSE and LEX log types
    def logger_callback(log_type: LogType, msg: str) -> None:
        context = {
            'source': 'tree-sitter',
            'type': 'parser',
            'log_type': 'parse' if log_type == LogType.PARSE else 'lex'
        }
        if log_type == LogType.PARSE:
            ts_logger.debug(msg, extra={'context': context})
        else:  # LEX
            ts_logger.info(msg, extra={'context': context})
    
    # Set the logger on the parser
    parser.set_logger_callback(logger_callback)
    
    return ts_logger 