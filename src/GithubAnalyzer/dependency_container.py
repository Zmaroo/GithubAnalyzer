"""Dependency injection container"""
from typing import Dict, Any, Type, Optional, Set
from dataclasses import dataclass
from .utils.errors import ServiceError
from .config.settings import settings
from .services.database_service import DatabaseService
from .services.graph_analysis_service import GraphAnalysisService
from .services.parser_service import ParserService
from .services.analyzer_service import AnalyzerService
from .services.framework_service import FrameworkService

@dataclass
class ServiceConfig:
    """Base configuration for all services"""
    name: str
    settings: Dict[str, Any]

@dataclass
class ServiceMetadata:
    """Service metadata including config and dependencies"""
    name: str
    dependencies: Set[str]
    config: ServiceConfig

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
        
    def validate_dependencies(self, dependencies: Set[str]) -> bool:
        """Validate that all dependencies exist"""
        return all(self.get(dep) is not None for dep in dependencies)

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
        
    def merge_config(self, name: str, override_config: Optional[Dict[str, Any]] = None) -> ServiceConfig:
        """Merge base config with overrides and create ServiceConfig"""
        base_config = self.get_config(name) or {}
        merged_settings = {**base_config, **(override_config or {})}
        return ServiceConfig(name=name, settings=merged_settings)

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
        
    @classmethod
    def bootstrap(cls) -> 'DependencyContainer':
        """Bootstrap all services in correct order"""
        container = cls.get_instance()
        
        # Register core services
        container.register('database', DatabaseService)
        container.register('parser', ParserService)
        
        # Register dependent services
        container.register('graph', GraphAnalysisService, 
                         dependencies={'database'})
        container.register('analyzer', AnalyzerService,
                         dependencies={'parser', 'graph'})
        container.register('framework', FrameworkService,
                         dependencies={'analyzer'})
        
        return container
        
    def register(self, name: str, service_class: Type[Any],
                config: Optional[Dict[str, Any]] = None,
                dependencies: Optional[Set[str]] = None) -> None:
        """Register a service with its dependencies"""
        if name in self._metadata:
            return  # Already registered
            
        # Validate and register dependencies first
        if dependencies and not self._registry.validate_dependencies(dependencies):
            missing = {dep for dep in (dependencies or set()) 
                      if not self._registry.get(dep)}
            raise ServiceError(f"Missing dependencies for {name}: {missing}")
                    
        # Create service config
        service_config = self._config_manager.merge_config(name, config)
        
        # Create and register service instance
        service_instance = service_class(self, service_config.settings)
        self._registry.register(name, service_instance)
        
        # Store metadata
        self._metadata[name] = ServiceMetadata(
            name=name,
            dependencies=dependencies or set(),
            config=service_config
        )
            
    def get_service(self, name: str) -> Any:
        """Get a registered service"""
        return self._registry.get(name)
        
    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get service configuration"""
        metadata = self._metadata.get(name)
        return metadata.config.settings if metadata else None 