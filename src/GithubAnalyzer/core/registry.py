"""Registry for managing services"""
from typing import Dict, Any
from .services.base import BaseService
from .services.database_service import DatabaseService
from ..utils.logging import setup_logger

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
                'database': DatabaseService(registry=self)
            }
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise
    
    @classmethod
    def create(cls) -> 'AnalysisToolRegistry':
        """Create registry instance"""
        return cls()
    
    def get_service(self, name: str) -> Any:
        """Get service by name"""
        return self.services.get(name) 