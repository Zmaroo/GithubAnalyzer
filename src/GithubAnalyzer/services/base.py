"""Base service class"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..dependency_container import DependencyContainer
from ..utils.errors import ServiceError

class BaseService(ABC):
    """Base class for all services"""
    
    def __init__(self, container: Optional[DependencyContainer] = None):
        self._container = container or DependencyContainer.get_instance()
        self.initialized = False
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize service"""
        pass
    
    def get_dependency(self, name: str) -> Any:
        """Get a service dependency"""
        service = self._container.get_service(name)
        if not service:
            raise ServiceError(f"Missing dependency: {name}")
        return service 