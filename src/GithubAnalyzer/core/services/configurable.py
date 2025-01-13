"""Configurable service base class"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from .base import BaseService, ServiceConfig, ServiceError

@dataclass
class DatabaseConfig(ServiceConfig):
    """Database service configuration"""
    host: str = 'localhost'
    port: int = 5432
    username: str = 'test'
    password: str = 'test'
    database: str = 'test'
    pool_size: int = 5

@dataclass
class GraphConfig(ServiceConfig):
    """Graph analysis service configuration"""
    neo4j_uri: str = 'bolt://localhost:7687'
    neo4j_user: str = 'neo4j'
    neo4j_password: str = 'password'
    graph_name: str = 'code_analysis'

class ConfigurableService(BaseService):
    """Base class for configurable services"""
    
    def __init__(self, registry: Optional['AnalysisToolRegistry'] = None,
                 config: Optional[ServiceConfig] = None):
        self._service_config = config
        super().__init__(registry)
        
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize with configuration"""
        if config:
            self._update_config(config)
            
    def _update_config(self, config: Dict[str, Any]) -> None:
        """Update service configuration"""
        if not self._service_config:
            return
            
        for key, value in config.items():
            if hasattr(self._service_config, key):
                setattr(self._service_config, key, value)
                
    @property
    def service_config(self) -> ServiceConfig:
        """Get service-specific configuration"""
        if not self._service_config:
            raise ServiceError("Service configuration not initialized")
        return self._service_config 