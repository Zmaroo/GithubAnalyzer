"""Base service class for all services"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, TYPE_CHECKING, Tuple
from dataclasses import dataclass
from ..utils.logging import setup_logger

if TYPE_CHECKING:
    from ..registry import AnalysisToolRegistry

logger = setup_logger(__name__)

class ServiceError(Exception):
    """Base exception for service errors"""
    pass

class FileParsingError(ServiceError):
    """Error during file parsing"""
    pass

class GraphAnalysisError(ServiceError):
    """Error during graph analysis"""
    pass

class DatabaseError(ServiceError):
    """Error during database operations"""
    pass

@dataclass
class ServiceContext:
    """Service initialization context"""
    registry: Optional['AnalysisToolRegistry'] = None
    config: Optional[Dict[str, Any]] = None

@dataclass
class ServiceConfig:
    """Base service configuration"""
    enabled: bool = True
    debug: bool = False
    timeout: int = 30
    retry_count: int = 3
    cache_enabled: bool = True

class BaseService(ABC):
    """Base class for all services"""
    
    def __init__(self, registry: Optional['AnalysisToolRegistry'] = None,
                 config: Optional[ServiceConfig] = None):
        self._registry = registry
        self._config = config or ServiceConfig()
        self.initialized = False
        self.error = None
        self.initialize()
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize service with optional config"""
        try:
            self._initialize(config)
            self.initialized = True
            logger.debug(f"Initialized {self.__class__.__name__}")
            return True
        except Exception as e:
            self._set_error(f"Failed to initialize: {e}")
            return False
    
    @abstractmethod
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize service-specific resources"""
        pass
    
    def cleanup(self) -> bool:
        """Cleanup resources"""
        try:
            self.initialized = False
            self._cleanup()
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup {self.__class__.__name__}: {e}")
            return False
            
    def _cleanup(self) -> None:
        """Service-specific cleanup"""
        pass
    
    def get_status(self) -> Tuple[bool, Optional[str]]:
        """Get service status and any error message"""
        return self.initialized, self.error
    
    def _set_error(self, error: str) -> None:
        """Set error state"""
        self.error = error
        self.initialized = False
        logger.error(f"Service error: {error}")
    
    def _clear_error(self) -> None:
        """Clear error state"""
        self.error = None
        
    @property
    def registry(self) -> 'AnalysisToolRegistry':
        """Get service registry"""
        if not self._registry:
            raise ServiceError("Registry not initialized")
        return self._registry
    
    @property
    def config(self) -> ServiceConfig:
        """Get service configuration"""
        return self._config
    
    def get_service(self, service_name: str) -> Optional['BaseService']:
        """Get service from registry"""
        try:
            return self.registry.get_service(service_name)
        except Exception as e:
            logger.error(f"Failed to get service {service_name}: {e}")
            return None 