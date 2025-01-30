try:
    from tree_sitter import Parser, Tree, QueryError
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
import json
import logging
import time
from typing import Optional, Union, Dict, Any, List
import sys
from datetime import datetime
import threading

from . import StructuredFormatter
"""Tree-sitter logging handler for GithubAnalyzer."""

class TreeSitterLogHandler(logging.Handler):
    """Handler for tree-sitter logging.
    
    This handler captures and stores log records from tree-sitter operations
    for testing and debugging purposes.
    """
    
    def __init__(self, name: str = "tree_sitter"):
        """Initialize the handler.
        
        Args:
            name: Base name for the logger
        """
        if not TREE_SITTER_AVAILABLE:
            raise ImportError("tree-sitter package is required for tree-sitter logging")
            
        super().__init__()
        self.name = name
        self.parse_records: List[logging.LogRecord] = []
        self.query_records: List[logging.LogRecord] = []
        self.error_records: List[logging.LogRecord] = []
        self._start_time = time.time()
        self._thread_id = threading.get_ident()
        self.formatter = StructuredFormatter()
        self.stream = sys.stdout
        self._enabled_parsers = set()
        self._enabled = False
        
    def enable(self) -> None:
        """Enable the handler."""
        self._enabled = True
        
    def disable(self) -> None:
        """Disable the handler."""
        self._enabled = False
        
    def clear(self) -> None:
        """Clear all stored records."""
        self.parse_records.clear()
        self.query_records.clear()
        self.error_records.clear()
        
    def _log(self, level: str, message: str, **kwargs) -> None:
        """Internal logging method.
        
        Args:
            level: Log level (debug, info, warning, error)
            message: Message to log
            **kwargs: Additional context
        """
        if self._enabled:
            record = logging.LogRecord(
                name=self.name,
                level=getattr(logging, level.upper()),
                pathname=__file__,
                lineno=0,
                msg=message,
                args=(),
                exc_info=None
            )
            record.context = kwargs
            self.handle(record)
        
    def handle(self, record: logging.LogRecord) -> bool:
        """Handle a log record.
        
        Args:
            record: The log record to handle
            
        Returns:
            True if the record was handled
        """
        # Add timing and thread info if not present
        if not hasattr(record, 'created'):
            record.created = time.time()
        if not hasattr(record, 'msecs'):
            record.msecs = (record.created - self._start_time) * 1000.0
        if not hasattr(record, 'thread'):
            record.thread = self._thread_id
        if not hasattr(record, 'threadName'):
            record.threadName = threading.current_thread().name
            
        # Get message context from record.context, message dictionary, or message itself
        msg_context = None
        msg_type = None
        msg_log_type = None
        
        # First check record.context
        if hasattr(record, 'context'):
            msg_context = record.context
            msg_type = msg_context.get('type')
            msg_log_type = msg_context.get('log_type')
        
        # Then check if message is a dictionary
        if isinstance(record.msg, dict):
            msg_dict = record.msg
            # Check for nested context in different formats
            if 'context' in msg_dict:
                msg_context = msg_dict['context']
            elif 'extra' in msg_dict and 'context' in msg_dict['extra']:
                msg_context = msg_dict['extra']['context']
            else:
                msg_context = msg_dict
            
            # Extract type information
            msg_type = msg_context.get('type')
            msg_log_type = msg_context.get('log_type')
        
        # Store record in appropriate list based on level and type
        is_error = (
            record.levelno >= logging.ERROR or 
            (msg_log_type and msg_log_type == 'error') or 
            (msg_type and msg_type == 'error') or
            (isinstance(record.msg, str) and 'error' in record.msg.lower()) or
            (msg_context and isinstance(msg_context, dict) and 
             (msg_context.get('log_type') == 'error' or 'error' in str(msg_context).lower()))
        )
        
        is_query = (
            (msg_type and msg_type == 'query') or 
            (msg_log_type and (msg_log_type in ['query', 'optimization'])) or
            (msg_context and isinstance(msg_context, dict) and 
             (msg_context.get('log_type') in ['query', 'optimization'] or 
              msg_context.get('type') == 'query')) or
            (isinstance(record.msg, str) and ('query' in record.msg.lower() or 'optimization' in record.msg.lower())) or
            (msg_context and isinstance(msg_context, dict) and 
             ('query' in str(msg_context).lower() or 'optimization' in str(msg_context).lower()))
        )
        
        if is_error:
            self.error_records.append(record)
        elif is_query:
            self.query_records.append(record)
        else:
            self.parse_records.append(record)
            
        return super().handle(record)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Process a log record.
        
        Args:
            record: The log record to process
        """
        # Format and write to stream if we have a formatter
        if self.formatter and self.stream:
            try:
                msg = self.formatter.format(record)
                self.stream.write(msg + '\n')
                self.stream.flush()
            except Exception:
                self.handleError(record)
    
    def __call__(self, log_type: int, message: Union[str, Dict[str, Any]]) -> None:
        """Handle tree-sitter parser callback logs (used by Parser.parse()).
        
        Args:
            log_type: Type of log message (0 for DEBUG, 1 for ERROR)
            message: The log message or dictionary containing log info
        """
        # Handle both string and dictionary messages
        if isinstance(message, dict):
            # For tree-sitter v24 format, the message is already structured
            msg_text = message.get('message', str(message))
            msg_context = message.get('context', {})
            
            # Extract type information from context
            msg_type = msg_context.get('type', 'parse')
            msg_log_type = msg_context.get('log_type', 'parse' if log_type == 0 else 'error')
            
            # Use the level from the message if available, but respect log_type
            level_name = message.get('level', 'ERROR' if log_type == 1 else 'DEBUG').upper()
            level = getattr(logging, level_name, logging.ERROR if log_type == 1 else logging.DEBUG)
            
            # Create record with the message's timestamp if available
            try:
                timestamp = datetime.fromisoformat(message.get('timestamp', datetime.now().isoformat())).timestamp()
            except (ValueError, TypeError):
                timestamp = time.time()
        else:
            msg_text = str(message)
            msg_type = 'parse'
            msg_log_type = 'error' if log_type == 1 else 'parse'
            msg_context = {}
            level = logging.ERROR if log_type == 1 else logging.DEBUG
            timestamp = time.time()

        # Create record with appropriate level and message
        record = logging.LogRecord(
            name=self.name,
            level=level,
            pathname="",
            lineno=0,
            msg=msg_text,  # Use the extracted message text
            args=(),
            exc_info=None
        )
        
        # Add context for structured logging
        record.context = {
            'source': 'tree-sitter',
            'type': msg_type,
            'log_type': msg_log_type,
            'logger': self.name,
            'level': logging.getLevelName(level),
            'duration_ms': (time.time() - self._start_time) * 1000.0,
            'timestamp': timestamp,
            **msg_context  # Include any additional context from the message
        }
        
        # Process the record through handle to ensure proper categorization
        self.handle(record)

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

    def log_tree_errors(self, tree: Tree, context: str = "") -> bool:
        """Log any errors in the tree using native tree-sitter error detection.
        
        Args:
            tree: The tree to check for errors
            context: Optional context string for the log message
            
        Returns:
            True if errors were found, False otherwise
        """
        if not self.name or not tree or not tree.root_node:
            return False

        has_errors = False
        prefix = f"{context}: " if context else ""

        # Create a log record for debug info
        debug_record = logging.LogRecord(
            name=f"{self.name}.parser",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg=f"{prefix}Validating tree with {tree.root_node.child_count} children",
            args=(),
            exc_info=None
        )
        debug_record.context = {
            'source': 'tree-sitter',
            'type': 'parser',
            'log_type': 'validation',
            'logger': f"{self.name}.parser",
            'level': 'DEBUG',
            'duration_ms': (time.time() - self._start_time) * 1000,
            'timestamp': time.time()
        }
        self.emit(debug_record)

        # Check for syntax errors
        if tree.root_node.has_error:
            has_errors = True
            error_msg = f"{prefix}Syntax error detected in tree"
            error_record = logging.LogRecord(
                name=f"{self.name}.parser",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg=error_msg,
                args=(),
                exc_info=None
            )
            error_record.context = {
                'source': 'tree-sitter',
                'type': 'parser',
                'log_type': 'error',
                'logger': f"{self.name}.parser",
                'level': 'ERROR',
                'duration_ms': (time.time() - self._start_time) * 1000,
                'timestamp': time.time()
            }
            self.emit(error_record)

        return has_errors

    def log_query_error(self, error: Union[QueryError, Exception], context: str = "") -> None:
        """Log a query-related error.
        
        Args:
            error: The error to log
            context: Optional context string for the log message
        """
        if not self.name:
            return

        prefix = f"{context}: " if context else ""
        logger = logging.getLogger(self.name)
        logger.error(f"{prefix}{str(error)}")

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        if self.name:
            logger = logging.getLogger(self.name)
            logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        if self.name:
            logger = logging.getLogger(self.name)
            logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        if self.name:
            logger = logging.getLogger(self.name)
            logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        if self.name:
            logger = logging.getLogger(self.name)
            logger.error(message, **kwargs)

    def critical(self, msg: str) -> None:
        """Log a critical message."""
        if self.name:
            logger = logging.getLogger(self.name)
            logger.critical(msg) 