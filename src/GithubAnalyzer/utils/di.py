"""Dependency injection container"""
from typing import Dict, Any, Type, Optional
from dataclasses import dataclass
from .services.base import BaseService
from .config import settings
from .errors import ServiceError

@dataclass
class ServiceRequirement:
    """Service requirement configuration from cursorrules"""
    name: str
    dependencies: list[str]
    config: Dict[str, Any]
    health_check: Optional[Dict[str, Any]] = None

class DependencyContainer:
    """Centralized dependency container"""
    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._requirements = self._load_requirements()
        self._initialization_order = settings.services.initialization_order

    def _load_requirements(self) -> Dict[str, ServiceRequirement]:
        """Load service requirements from cursorrules"""
        return {
            name: ServiceRequirement(
                name=name,
                dependencies=svc.get('dependencies', []),
                config=svc.get('config', {}),
                health_check=svc.get('health_check')
            )
            for name, svc in settings.services.required_services.items()
        }

    def initialize_services(self) -> None:
        """Initialize services in correct order"""
        for service_name in self._initialization_order:
            if service_name not in self._services:
                self._initialize_service(service_name)

    def _initialize_service(self, name: str) -> None:
        """Initialize a service and its dependencies"""
        req = self._requirements.get(name)
        if not req:
            raise ServiceError(f"No requirements for {name}")

        # Initialize dependencies first
        for dep in req.dependencies:
            if dep not in self._services:
                self._initialize_service(dep)

        # Initialize service
        service_class = self._get_service_class(name)
        self._services[name] = service_class(self, req.config)

    def register(self, name: str, service: Type[BaseService],
                config: Optional[Dict[str, Any]] = None) -> None:
        """Register a service with validation"""
        if name not in self._services:
            # Get requirements
            requirements = self._requirements.get(name)
            if not requirements:
                raise ServiceError(f"No requirements defined for {name}")
                
            # Validate dependencies
            for dep in requirements.dependencies:
                if dep not in self._services:
                    raise ServiceError(f"Missing dependency {dep} for {name}")
                    
            # Merge configs
            merged_config = {
                **requirements.config,
                **(config or {})
            }
            
            # Initialize service
            self._services[name] = service(self, merged_config)
            self._configs[name] = merged_config
            
    def get_service(self, name: str) -> Optional[BaseService]:
        """Get a registered service"""
        return self._services.get(name)
        
    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get service configuration"""
        return self._configs.get(name) 