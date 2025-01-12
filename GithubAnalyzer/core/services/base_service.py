from abc import ABC, abstractmethod
from typing import Optional
from ..registry import BusinessTools

class BaseService(ABC):
    """Base class for all services"""
    
    def __init__(self, tools: Optional[BusinessTools] = None):
        self.tools = tools
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize service-specific resources"""
        pass 