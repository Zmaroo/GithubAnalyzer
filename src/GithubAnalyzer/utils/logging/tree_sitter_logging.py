from tree_sitter import LogType, Parser, Tree, QueryError
import json
import logging
import time
from typing import Optional, Union, Dict, Any
import sys
from datetime import datetime

from .formatters import StructuredFormatter
"""Tree-sitter logging handler for GithubAnalyzer."""

class TreeSitterLogHandler(logging.Handler):
    """Custom logging handler for tree-sitter operations.
    
    This handler formats tree-sitter logs with structured context and timing information.
    """
    
    def __init__(self, logger_name: str = 'tree_sitter') -> None:
        """Initialize the handler with a structured formatter.
        
        Args:
            logger_name: The name of the logger to use. Defaults to 'tree_sitter'.
        """
        super().__init__()
        self.formatter = StructuredFormatter()
        self.start_time = time.time()
        self.logger_name = logger_name
        self.stream = sys.stdout
        
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record with structured context and timing.
        
        Args:
            record: The log record to emit.
        """
        try:
            # Add timing information
            duration = time.time() - self.start_time
            if not hasattr(record, 'duration_ms'):
                record.duration_ms = duration * 1000
                
            # Add context if not present
            if not hasattr(record, 'context'):
                record.context = {}
                
            # Add tree-sitter specific context
            record.context.update({
                'logger': record.name,
                'level': record.levelname,
                'duration_ms': record.duration_ms,
                'timestamp': record.created
            })
            
            # Format and emit the record
            msg = self.format(record)
            self.stream.write(msg + '\n')
            self.flush()
            
        except Exception as e:
            self.handleError(record)
            
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record using the structured formatter.
        
        Args:
            record: The log record to format.
            
        Returns:
            The formatted log message.
        """
        if self.formatter:
            return self.formatter.format(record)
        return str(record.msg)

    def enable_parser_logging(self, parser: Parser) -> None:
        """Enable logging for a parser.
        
        Args:
            parser: The parser to enable logging for
        """
        if hasattr(parser, 'log'):
            parser.logger = self
            parser.log = self.__call__
        
    def disable_parser_logging(self, parser: Parser) -> None:
        """Disable logging for a parser.
        
        Args:
            parser: The parser to disable logging for
        """
        try:
            if hasattr(parser, "logger"):
                parser.logger = None
                if hasattr(parser, 'log'):
                    parser.log = None
                delattr(parser, "logger")
        except AttributeError:
            # Ignore if we can't remove the logger
            pass

    def log_tree_errors(self, tree: Tree, context: str = "") -> bool:
        """Log any errors in the tree using native tree-sitter error detection.
        
        Args:
            tree: The tree to check for errors
            context: Optional context string for the log message
            
        Returns:
            True if errors were found, False otherwise
        """
        if not self.logger_name or not tree or not tree.root_node:
            return False

        has_errors = False
        prefix = f"{context}: " if context else ""

        # Log detailed node information in debug mode
        logger = logging.getLogger(self.logger_name)
        logger.debug(f"{prefix}Validating tree with {tree.root_node.child_count} children")

        # Check for syntax errors
        if tree.root_node.has_error:
            logger.error(f"{prefix}Tree contains syntax errors")
            if logger.isEnabledFor(logging.DEBUG):
                # Log more details about the error nodes
                cursor = tree.walk()
                while cursor.goto_first_child() or cursor.goto_next_sibling():
                    node = cursor.node
                    if node.has_error:
                        logger.debug(f"{prefix}Error node at {node.start_point}-{node.end_point}: {node.type}")
            has_errors = True

        # Check for missing nodes
        cursor = tree.walk()
        while cursor.goto_first_child() or cursor.goto_next_sibling():
            node = cursor.node
            if node.is_missing:
                logger.error(f"{prefix}Tree contains missing node at {node.start_point}")
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"{prefix}Missing node details: type={node.type}, parent={node.parent.type if node.parent else 'None'}")
                has_errors = True
                break

        return has_errors

    def log_query_error(self, error: Union[QueryError, Exception], context: str = "") -> None:
        """Log a query-related error.
        
        Args:
            error: The error to log
            context: Optional context string for the log message
        """
        if not self.logger_name:
            return

        prefix = f"{context}: " if context else ""
        logger = logging.getLogger(self.logger_name)
        logger.error(f"{prefix}{str(error)}")

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        if self.logger_name:
            logger = logging.getLogger(self.logger_name)
            logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        if self.logger_name:
            logger = logging.getLogger(self.logger_name)
            logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        if self.logger_name:
            logger = logging.getLogger(self.logger_name)
            logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        if self.logger_name:
            logger = logging.getLogger(self.logger_name)
            logger.error(message, **kwargs)

    def critical(self, msg: str) -> None:
        """Log a critical message."""
        if self.logger_name:
            logger = logging.getLogger(self.logger_name)
            logger.critical(msg)

    def enable(self) -> None:
        """Enable logging."""
        self.setLevel(logging.DEBUG)

    def disable(self) -> None:
        """Disable logging."""
        self.setLevel(logging.INFO) 