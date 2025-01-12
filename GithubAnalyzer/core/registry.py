"""Registry for analysis tools and services"""
from typing import Dict, Any, Callable
from dataclasses import dataclass
from .services import (
    ParserService,
    AnalyzerService,
    DatabaseService,
    FrameworkService
)
from .utils.logging import setup_logger

logger = setup_logger(__name__)

@dataclass
class AnalysisToolRegistry:
    """Central registry for all analysis tools and services"""
    parser_service: ParserService
    analyzer_service: AnalyzerService
    database_service: DatabaseService
    framework_service: FrameworkService

    @classmethod
    def create(cls) -> 'AnalysisToolRegistry':
        """Factory method to create properly initialized tools"""
        try:
            # Create services in dependency order
            database_service = DatabaseService()
            parser_service = ParserService()
            framework_service = FrameworkService()
            analyzer_service = AnalyzerService()
            
            # Initialize registry
            registry = cls(
                parser_service=parser_service,
                analyzer_service=analyzer_service,
                database_service=database_service,
                framework_service=framework_service
            )
            
            # Set registry reference in each service
            for service in registry.__dict__.values():
                service.registry = registry
                
            return registry
            
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