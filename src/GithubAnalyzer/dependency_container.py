"""Dependency injection container"""
from typing import Dict, Any, Type, Optional, Set
from dataclasses import dataclass
from .utils.errors import ServiceError
from .config.settings import settings

@dataclass
class ServiceMetadata:
    """Service metadata for dependency management"""
    name: str
    dependencies: Set[str]
    config: Dict[str, Any]

class ServiceRegistry:
    """Registry for managing service instances"""
    def __init__(self):
        self._services: Dict[str, Any] = {}
        
    def register(self, name: str, service: Any) -> None:
        """Register a service instance"""
        self._services[name] = service
        
    def get(self, name: str) -> Optional[Any]:
        """Get a registered service"""
        return self._services.get(name)

class ConfigurationManager:
    """Manager for service configurations"""
    def __init__(self):
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._load_configurations()
        
    def _load_configurations(self) -> None:
        """Load configurations from settings"""
        self._configs = settings.SERVICE_SETTINGS
        
    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a service"""
        return self._configs.get(name)
        
    def merge_config(self, name: str, override_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Merge base config with overrides"""
        base_config = self.get_config(name) or {}
        if override_config:
            return {**base_config, **override_config}
        return base_config

class DependencyContainer:
    """Centralized dependency container"""
    _instance = None
    
    def __init__(self):
        self._registry = ServiceRegistry()
        self._config_manager = ConfigurationManager()
        self._metadata: Dict[str, ServiceMetadata] = {}
        
    @classmethod
    def get_instance(cls) -> 'DependencyContainer':
        """Get singleton instance"""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
        
    def register(self, name: str, service_class: Type[Any],
                config: Optional[Dict[str, Any]] = None,
                dependencies: Optional[Set[str]] = None) -> None:
        """Register a service with its dependencies"""
        if name in self._metadata:
            return  # Already registered
            
        # Validate and register dependencies first
        if dependencies:
            for dep in dependencies:
                if not self._registry.get(dep):
                    raise ServiceError(f"Missing dependency {dep} for {name}")
                    
        # Merge configuration
        merged_config = self._config_manager.merge_config(name, config)
        
        # Create and register service instance
        service_instance = service_class(self, merged_config)
        self._registry.register(name, service_instance)
        
        # Store metadata
        self._metadata[name] = ServiceMetadata(
            name=name,
            dependencies=dependencies or set(),
            config=merged_config
        )
            
    def get_service(self, name: str) -> Any:
        """Get a registered service"""
        return self._registry.get(name)
        
    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get service configuration"""
        return self._config_manager.get_config(name) 