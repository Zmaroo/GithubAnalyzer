"""Base service class for all services"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, TYPE_CHECKING
from ..utils.logging import setup_logger

if TYPE_CHECKING:
    from ..registry import AnalysisToolRegistry

logger = setup_logger(__name__)

class BaseService(ABC):
    """Base class for all services"""
    
    def __init__(self, registry: Optional['AnalysisToolRegistry'] = None):
        self.registry = registry
        self.initialized = False
        self.error = None
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize service with optional config"""
        try:
            self._initialize(config)
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            return False
    
    @abstractmethod
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize service-specific resources"""
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """Cleanup resources"""
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