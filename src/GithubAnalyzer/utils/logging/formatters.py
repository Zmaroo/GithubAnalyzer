"""Logging formatters."""

import json
import logging
from typing import Any, Dict, Optional

class StructuredFormatter(logging.Formatter):
    """Formatter that outputs JSON formatted logs."""
    
    def __init__(self, fmt: Optional[str] = None):
        """Initialize formatter.
        
        Args:
            fmt: Optional format string
        """
        super().__init__()
        self.fmt = fmt or json.dumps({
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "logger": "%(name)s",
            "message": "%(message)s"
        })
        
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted string
        """
        # Create a copy of the record to avoid modifying the original
        record_dict = record.__dict__.copy()
        
        # Convert the message to a dict if it isn't already
        if isinstance(record_dict["msg"], dict):
            message = record_dict["msg"]
        else:
            message = {"message": str(record_dict["msg"])}
            
        # Add standard fields
        message.update({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name
        })
        
        # Add context if present
        if hasattr(record, "context"):
            message["context"] = record.context
            
        return json.dumps(message) 