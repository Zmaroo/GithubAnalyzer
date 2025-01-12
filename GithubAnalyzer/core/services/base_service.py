"""Base service implementation"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..registry import AnalysisToolRegistry
from ..utils.logging import setup_logger
from dataclasses import dataclass

logger = setup_logger(__name__)

@dataclass
class ServiceContext:
    """Service initialization context"""
    registry: Optional[AnalysisToolRegistry] = None
    config: Optional[Dict[str, Any]] = None

class BaseService(ABC):
    """Base class for all services"""
    
    def __init__(self, context: Optional[ServiceContext] = None):
        self.context = context or ServiceContext()
        self._initialize()
        logger.debug(f"Initialized {self.__class__.__name__}")
    
    @property
    def registry(self) -> Optional[AnalysisToolRegistry]:
        return self.context.registry
        
    @property
    def config(self) -> Dict[str, Any]:
        return self.context.config or {}

    @abstractmethod
    def _initialize(self) -> None:
        """Initialize service-specific resources"""
        pass

    def cleanup(self) -> None:
        """Clean up service resources"""
        pass 