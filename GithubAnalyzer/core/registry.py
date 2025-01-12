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
class BusinessTools:
    """Single source of truth for all business tools"""
    parser_service: ParserService
    analyzer_service: AnalyzerService
    database_service: DatabaseService
    framework_service: FrameworkService

    @classmethod
    def create(cls) -> 'BusinessTools':
        """Factory method to create properly initialized tools"""
        # Create services
        database_service = DatabaseService()
        parser_service = ParserService()
        framework_service = FrameworkService()
        analyzer_service = AnalyzerService()
        
        # Initialize cross-service dependencies
        tools = cls(
            parser_service=parser_service,
            analyzer_service=analyzer_service,
            database_service=database_service,
            framework_service=framework_service
        )
        
        # Set tools reference in each service
        for service in [parser_service, analyzer_service, 
                       database_service, framework_service]:
            service.tools = tools
            
        return tools

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