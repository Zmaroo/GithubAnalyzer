"""Tree-sitter logging handler."""
import logging
from typing import Optional, Union, Dict, Any
from tree_sitter import LogType, Parser, Tree, QueryError
import sys

class TreeSitterLogHandler(logging.Handler):
    """Handler for tree-sitter logging that maps log types to Python logging levels."""
    
    def __init__(self, logger_name: str = "tree_sitter"):
        """Initialize the log handler.
        
        Args:
            logger_name: Name of the logger to use
        """
        super().__init__()
        self.logger_name = logger_name
        self.setLevel(logging.DEBUG)
        
        # Map tree-sitter log types to Python logging levels
        self._log_type_map = {
            LogType.PARSE: logging.DEBUG,  # Detailed parse operations
            LogType.LEX: logging.DEBUG,    # Detailed lexing operations
        }
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        try:
            # Get the root logger
            logger = logging.getLogger(self.logger_name)
            msg = self.format(record)
            logger.log(record.levelno, msg)
        except Exception:
            self.handleError(record)
            
    def __call__(self, log_type: LogType, message: str) -> None:
        """Handle a log message from tree-sitter."""
        level = self._log_type_map.get(log_type, logging.INFO)
        logger = logging.getLogger(self.logger_name)
        logger.log(level, message)
        
    def enable_parser_logging(self, parser: Parser) -> None:
        """Enable logging for a parser.
        
        Args:
            parser: The parser to enable logging for
        """
        parser.logger = self
        
    def disable_parser_logging(self, parser: Parser) -> None:
        """Disable logging for a parser.
        
        Args:
            parser: The parser to disable logging for
        """
        try:
            if hasattr(parser, "logger"):
                parser.logger = None
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