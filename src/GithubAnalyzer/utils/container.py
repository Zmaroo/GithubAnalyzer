"""Dependency injection container"""
from typing import Dict, Any, Type, Optional, Set
from .services.base import BaseService
from .config.settings import settings
from .services.errors import ServiceError

class ServiceContainer:
    """Service container for dependency injection"""
    
    _instance = None
    _services: Dict[str, BaseService] = {}
    _configs: Dict[str, Any] = {}
    _dependencies: Dict[str, Set[str]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, name: str, service_class: Type[BaseService], 
                config: Optional[Any] = None, dependencies: Optional[Set[str]] = None) -> None:
        """Register a service with its dependencies"""
        if name in self._services:
            return
            
        # Check dependencies first
        if dependencies:
            self._dependencies[name] = dependencies
            for dep in dependencies:
                if dep not in self._services:
                    raise ServiceError(f"Dependency {dep} not registered for {name}")
        
        # Create service with config
        service_config = config or self._get_default_config(name)
        self._services[name] = service_class(self, service_config)
        self._configs[name] = service_config
    
    def _get_default_config(self, service_name: str) -> Dict[str, Any]:
        """Get default configuration for service"""
        if service_name == 'database':
            return settings.DATABASE_SETTINGS
        elif service_name == 'graph':
            return settings.GRAPH_SETTINGS
        elif service_name == 'analyzer':
            return settings.ANALYSIS_SETTINGS
        return {}
    
    def get(self, name: str) -> Optional[BaseService]:
        """Get a service by name"""
        service = self._services.get(name)
        if not service and name in self._dependencies:
            self._init_dependencies(name)
            service = self._services.get(name)
        return service
    
    def _init_dependencies(self, name: str) -> None:
        """Initialize service dependencies"""
        if name not in self._dependencies:
            return
            
        for dep in self._dependencies[name]:
            if dep not in self._services:
                self._init_dependencies(dep)
    
    def get_config(self, name: str) -> Optional[Any]:
        """Get service configuration"""
        return self._configs.get(name)
    
    def validate_dependencies(self) -> bool:
        """Validate all service dependencies are met"""
        for service, deps in self._dependencies.items():
            for dep in deps:
                if dep not in self._services:
                    return False
        return True 