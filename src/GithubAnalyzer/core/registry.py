"""Registry for managing services"""
from typing import Dict, Any
from .services.base import BaseService
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
        self._initialize_services()
        
    def _initialize_services(self):
        """Initialize all services"""
        # Initialize core services
        self.services['database'] = DatabaseService(self)
        self.services['parser'] = ParserService(self)
        self.services['analyzer'] = AnalyzerService(self)
        self.services['framework'] = FrameworkService(self)
        self.services['graph'] = GraphAnalysisService(self)
        
        # Initialize each service
        for service in self.services.values():
            service.initialize()
            
        # Create common operations interface
        self.common_operations = CommonOperations(self)
    
    @property
    def database_service(self) -> DatabaseService:
        """Get database service"""
        return self.services['database']
        
    @property
    def parser_service(self) -> ParserService:
        """Get parser service"""
        return self.services['parser']
        
    @property
    def analyzer_service(self) -> AnalyzerService:
        """Get analyzer service"""
        return self.services['analyzer']
        
    @property
    def framework_service(self) -> FrameworkService:
        """Get framework service"""
        return self.services['framework']
        
    @property
    def graph_service(self) -> GraphAnalysisService:
        """Get graph analysis service"""
        return self.services['graph']
    
    def get_common_operations(self) -> CommonOperations:
        """Get common operations interface"""
        return self.common_operations
    
    @classmethod
    def create(cls) -> 'AnalysisToolRegistry':
        """Create registry instance"""
        return cls()
    
    def get_service(self, name: str) -> Any:
        """Get service by name"""
        return self.services.get(name) 