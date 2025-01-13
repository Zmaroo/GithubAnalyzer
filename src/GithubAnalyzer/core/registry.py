"""Registry for managing services"""
from typing import Dict, Any, List
from .services.base import BaseService
from .services.database_service import DatabaseService
from .services.graph_analysis_service import GraphAnalysisService
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
        try:
            self.services = {
                'database': DatabaseService(registry=self),
                'graph_analysis': GraphAnalysisService(registry=self)
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
    
    def get_common_operations(self) -> List[str]:
        """Get list of common operations"""
        return [
            'parse_file',
            'analyze_dependencies',
            'check_security',
            'validate_syntax'
        ]
    
    @classmethod
    def create(cls) -> 'AnalysisToolRegistry':
        """Create registry instance"""
        return cls()
    
    def get_service(self, name: str) -> Any:
        """Get service by name"""
        return self.services.get(name) 