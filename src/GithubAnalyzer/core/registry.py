"""Registry for managing services"""
from typing import Dict, Any
from .services.base import BaseService
from .services.database_service import DatabaseService
from .services.graph_analysis_service import GraphAnalysisService
from .services.parser_service import ParserService
from .operations import CommonOperations
from .utils.logging import setup_logger

logger = setup_logger(__name__)

class AnalysisToolRegistry:
    """Registry for managing analysis tools and services"""
    
    def __init__(self):
        """Initialize registry"""
        self.services: Dict[str, BaseService] = {}
        self._initialize_services()
        self.common_operations = CommonOperations(self)
        
    def _initialize_services(self):
        """Initialize all services"""
        try:
            self.services = {
                'database': DatabaseService(registry=self),
                'graph_analysis': GraphAnalysisService(registry=self),
                'parser': ParserService(registry=self)
            }
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    @property
    def database_service(self) -> DatabaseService:
        """Get database service"""
        return self.services['database']
        
    @property
    def graph_analysis_service(self) -> GraphAnalysisService:
        """Get graph analysis service"""
        return self.services['graph_analysis']
        
    @property
    def parser_service(self) -> ParserService:
        """Get parser service"""
        return self.services['parser']
    
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