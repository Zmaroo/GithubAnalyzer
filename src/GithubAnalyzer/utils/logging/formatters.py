"""Logging formatters for GithubAnalyzer."""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """Format log records as structured JSON with context."""
    
    def __init__(self, indent: Optional[int] = None):
        """Initialize formatter.
        
        Args:
            indent: Optional JSON indentation level
        """
        super().__init__()
        self.indent = indent
        
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON with context.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON formatted string
        """
        # Extract message and context
        if isinstance(record.msg, dict):
            message = record.msg.get("message", str(record.msg))
            context = record.msg.get("context", {})
        else:
            message = str(record.msg)
            context = getattr(record, 'context', {})
            
        # Build output dictionary
        output = {
            "message": message,
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add duration if available
        if hasattr(record, 'duration_ms'):
            output['duration_ms'] = record.duration_ms
            
        # Add context if present
        if context:
            # Format nested dictionaries
            if isinstance(context, dict):
                for key, value in context.items():
                    if isinstance(value, dict):
                        context[key] = json.dumps(value, indent=2)
            output["context"] = context
            
        # Add exception info if present
        if record.exc_info:
            output["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(output, indent=self.indent) 