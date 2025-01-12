"""Base service implementation"""
from abc import ABC, abstractmethod
from typing import Optional
from ..registry import AnalysisToolRegistry
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class BaseService(ABC):
    """Base class for all services"""
    
    def __init__(self, registry: Optional[AnalysisToolRegistry] = None):
        self.registry = registry
        self._initialize()
        logger.debug(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize service-specific resources"""
        pass

    def cleanup(self) -> None:
        """Clean up service resources"""
        pass 