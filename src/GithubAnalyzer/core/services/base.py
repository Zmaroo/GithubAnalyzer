"""Base service class for all services"""
from abc import ABC, abstractmethod
from typing import Optional
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class BaseService(ABC):
    """Base class for all services"""
    
    def __init__(self):
        """Initialize service"""
        self.initialized = False
        self.error = None
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the service. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """Cleanup resources. Must be implemented by subclasses."""
        pass
    
    def get_status(self) -> tuple[bool, Optional[str]]:
        """Get service status and any error message"""
        return self.initialized, self.error
    
    def _set_error(self, error: str):
        """Set error state"""
        self.error = error
        self.initialized = False
        logger.error(f"Service error: {error}")
    
    def _clear_error(self):
        """Clear error state"""
        self.error = None 