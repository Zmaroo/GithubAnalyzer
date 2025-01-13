"""Registry for managing services"""
from typing import Dict, Any, Optional, Type
from .services.base import BaseService, ServiceConfig
from .services.configurable import (
    DatabaseConfig, GraphConfig, ParserConfig,
    AnalyzerConfig, FrameworkConfig
)
from .services.database_service import DatabaseService
from .services.graph_analysis_service import GraphAnalysisService
from .services.parser_service import ParserService
from .services.analyzer_service import AnalyzerService
from .services.framework_service import FrameworkService
from .container import ServiceContainer
from .utils.logging import setup_logger

logger = setup_logger(__name__)

class AnalysisToolRegistry:
    """Registry for managing analysis tools and services"""
    
    def __init__(self):
        """Initialize registry"""
        self.container = ServiceContainer()
        self._register_services()
        
    def _register_services(self) -> None:
        """Register all services with dependencies"""
        # Register base services first
        self.container.register('database', DatabaseService, 
                              config=DatabaseConfig())
        
        self.container.register('parser', ParserService,
                              config=ParserConfig())
        
        # Register dependent services
        self.container.register('graph', GraphAnalysisService,
                              config=GraphConfig(),
                              dependencies={'database'})
        
        self.container.register('analyzer', AnalyzerService,
                              config=AnalyzerConfig(),
                              dependencies={'parser', 'graph'})
        
        self.container.register('framework', FrameworkService,
                              config=FrameworkConfig(),
                              dependencies={'analyzer'})
        
        # Validate all dependencies
        if not self.container.validate_dependencies():
            raise RuntimeError("Service dependencies validation failed")
    
    def get_service(self, name: str) -> Optional[BaseService]:
        """Get service by name"""
        return self.container.get(name)
        
    def get_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get service configuration"""
        return self.container.get_config(service_name)

    @classmethod
    def create(cls) -> 'AnalysisToolRegistry':
        """Create registry instance"""
        return cls() 