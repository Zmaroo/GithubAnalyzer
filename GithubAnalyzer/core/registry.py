"""Registry for analysis tools and services"""
from typing import Dict, Any, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class AnalysisToolRegistry:
    """Central registry for all analysis tools and services"""
    
    def __init__(self):
        self._services = {}
        self._initialize_services()
    
    def _initialize_services(self) -> None:
        """Initialize all services"""
        from .services.parser_service import ParserService
        from .services.analyzer_service import AnalyzerService
        from .services.database_service import DatabaseService
        from .services.framework_service import FrameworkService
        from .services.graph_analysis_service import GraphAnalysisService
        
        self._services = {
            'parser_service': ParserService(self),
            'analyzer_service': AnalyzerService(self),
            'database_service': DatabaseService(self),
            'framework_service': FrameworkService(self),
            'graph_analysis_service': GraphAnalysisService(self)
        }
    
    @property
    def parser_service(self):
        return self._services['parser_service']
        
    @property
    def analyzer_service(self):
        return self._services['analyzer_service']
        
    @property
    def database_service(self):
        return self._services['database_service']
        
    @property
    def framework_service(self):
        return self._services['framework_service']
        
    @property
    def graph_analysis_service(self):
        return self._services['graph_analysis_service']
    
    @classmethod
    def create(cls) -> 'AnalysisToolRegistry':
        """Factory method to create properly initialized tools"""
        try:
            return cls()
        except Exception as e:
            logger.error(f"Failed to create tool registry: {e}")
            raise

    def get_tools(self) -> Dict[str, Callable]:
        """Get all available tools"""
        return {
            # Analysis tools
            "analyze_repository": self.analyzer_service.analyze_repository,
            "analyze_file": self.analyzer_service.analyze_file,
            
            # Database tools
            "store_analysis": self.database_service.store_analysis,
            "get_analysis": self.database_service.get_analysis,
            
            # Parser tools
            "parse_file": self.parser_service.parse_file,
            
            # Framework tools
            "detect_frameworks": self.framework_service.detect_frameworks
        } 