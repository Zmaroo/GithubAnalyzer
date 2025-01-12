"""Base service implementation"""
from __future__ import annotations  # Enable forward references
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass
import logging

if TYPE_CHECKING:
    from ..registry import AnalysisToolRegistry

logger = logging.getLogger(__name__)

@dataclass
class ServiceContext:
    """Service initialization context"""
    registry: Optional['AnalysisToolRegistry'] = None
    config: Optional[Dict[str, Any]] = None

class BaseService(ABC):
    """Base class for all services"""
    
    def __init__(self, registry: Optional['AnalysisToolRegistry'] = None):
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