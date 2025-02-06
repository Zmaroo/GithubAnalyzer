"""Base model for all models in the application."""
from dataclasses import dataclass
from typing import Any, Dict, Optional

from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class BaseModel:
    """Base class for all models."""
    
    def __post_init__(self) -> None:
        """Initialize the model."""
        pass
    
    def _log(self, level: str, message: str, **kwargs) -> None:
        """Log a message with context.
        
        Args:
            level: Log level (debug, info, warning, error)
            message: Message to log
            **kwargs: Additional context
        """
        context = {
            'model': self.__class__.__name__,
            **kwargs
        }
        
        getattr(logger, level)(message, extra={'context': context}) 