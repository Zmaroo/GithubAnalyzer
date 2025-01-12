"""Registry for analysis tools and services"""
from __future__ import annotations
from typing import Dict, Any, Callable, TYPE_CHECKING, Protocol
from dataclasses import dataclass
import logging

if TYPE_CHECKING:
    from .services.parser_service import ParserService
    from .services.analyzer_service import AnalyzerService
    from .services.database_service import DatabaseService
    from .services.framework_service import FrameworkService
    from .services.graph_analysis_service import GraphAnalysisService
    from .models import (
        ModuleInfo,
        RepositoryInfo,
        AnalysisResult
    )

logger = logging.getLogger(__name__)

class AnalysisOperations(Protocol):
    """Protocol defining common analysis operations"""
    def analyze_repository(self, path: str) -> RepositoryInfo: ...
    def analyze_file(self, path: str) -> ModuleInfo: ...
    def store_analysis(self, analysis: AnalysisResult) -> bool: ...
    def get_analysis(self, id: str) -> AnalysisResult: ...
    def parse_file(self, path: str, content: str) -> ModuleInfo: ...
    def detect_frameworks(self, module: ModuleInfo) -> list[str]: ...

@dataclass
class CommonOperations:
    """Common operations facade for simplified access to core functionality"""
    analyze_repository: Callable[[str], RepositoryInfo]
    analyze_file: Callable[[str], ModuleInfo]
    store_analysis: Callable[[AnalysisResult], bool]
    get_analysis: Callable[[str], AnalysisResult]
    parse_file: Callable[[str, str], ModuleInfo]
    detect_frameworks: Callable[[ModuleInfo], list[str]]

@dataclass
class AnalysisToolRegistry:
    """Central registry for managing analysis services and their lifecycle"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialize_services()
    
    def _initialize_services(self) -> None:
        """Initialize all services"""
        # Import services here to avoid circular imports
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
    def parser_service(self) -> 'ParserService':
        return self._services['parser_service']
        
    @property
    def analyzer_service(self) -> 'AnalyzerService':
        return self._services['analyzer_service']
        
    @property
    def database_service(self) -> 'DatabaseService':
        return self._services['database_service']
        
    @property
    def framework_service(self) -> 'FrameworkService':
        return self._services['framework_service']
        
    @property
    def graph_analysis_service(self) -> 'GraphAnalysisService':
        return self._services['graph_analysis_service']
    
    def get_common_operations(self) -> CommonOperations:
        """Get simplified interface for common operations"""
        return CommonOperations(
            analyze_repository=self.analyzer_service.analyze_repository,
            analyze_file=self.analyzer_service.analyze_file,
            store_analysis=self.database_service.store_analysis,
            get_analysis=self.database_service.get_analysis,
            parse_file=self.parser_service.parse_file,
            detect_frameworks=self.framework_service.detect_frameworks
        )
    
    @classmethod
    def create(cls) -> 'AnalysisToolRegistry':
        """Factory method to create properly initialized tools"""
        try:
            return cls()
        except Exception as e:
            logger.error(f"Failed to create tool registry: {e}")
            raise 