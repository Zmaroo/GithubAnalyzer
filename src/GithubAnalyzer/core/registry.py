"""Registry for managing services"""
from typing import Dict, Any, Optional, Type
from .services.base import BaseService, ServiceConfig
from .services.configurable import DatabaseConfig, GraphConfig
from .services.database_service import DatabaseService
from .services.graph_analysis_service import GraphAnalysisService
from .services.parser_service import ParserService
from .services.analyzer_service import AnalyzerService
from .services.framework_service import FrameworkService
from .operations import CommonOperations
from .utils.logging import setup_logger

logger = setup_logger(__name__)

class AnalysisToolRegistry:
    """Registry for managing analysis tools and services"""
    
    def __init__(self):
        """Initialize registry"""
        self.services: Dict[str, BaseService] = {}
        self._service_configs: Dict[str, ServiceConfig] = self._get_default_configs()
        self._initialize_services()
        
    def _get_default_configs(self) -> Dict[str, ServiceConfig]:
        """Get default service configurations"""
        return {
            'database': DatabaseConfig(),
            'graph': GraphConfig(),
            'parser': ServiceConfig(),
            'analyzer': ServiceConfig(),
            'framework': ServiceConfig()
        }
        
    def _initialize_services(self) -> None:
        """Initialize all services"""
        service_classes = {
            'database': DatabaseService,
            'parser': ParserService,
            'analyzer': AnalyzerService,
            'framework': FrameworkService,
            'graph': GraphAnalysisService
        }
        
        # Initialize each service with its config
        for name, service_class in service_classes.items():
            config = self._service_configs.get(name)
            self.services[name] = service_class(self, config)
            
        # Create common operations interface
        self.common_operations = CommonOperations(self)
    
    def get_service(self, name: str) -> Optional[BaseService]:
        """Get service by name"""
        return self.services.get(name)
        
    def get_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get service configuration"""
        return self._service_configs.get(service_name) 