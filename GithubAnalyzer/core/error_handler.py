"""Centralized error handling"""
from typing import Optional, Dict, Any, Type
from .models.errors import AnalysisError
from functools import wraps
import logging
import traceback

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def handle(
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        error_type: Type[AnalysisError] = AnalysisError
    ) -> AnalysisError:
        """Convert exception to AnalysisError"""
        logger.error(f"Error: {error}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        
        return error_type(
            message=str(error),
            code=error.__class__.__name__,
            details=context,
            source=traceback.extract_tb(error.__traceback__)[-1].filename
        )

def handle_errors(error_type: Type[AnalysisError] = AnalysisError):
    """Decorator for error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return ErrorHandler.handle(e, error_type=error_type)
        return wrapper
    return decorator 