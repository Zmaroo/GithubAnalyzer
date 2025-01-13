"""Service operations"""
from typing import Optional
from .base import BaseService
from ..models import ModuleInfo, AnalysisResult
from ..errors import ServiceError

class OperationsService(BaseService):
    """Core operations service"""
    
    def _initialize(self) -> None:
        """Initialize required services"""
        self.parser = self.get_dependency('parser')
        self.analyzer = self.get_dependency('analyzer')
        self.database = self.get_dependency('database')
        
    def analyze_file(self, file_path: str) -> Optional[ModuleInfo]:
        """Analyze a single file"""
        try:
            result = self.parser.parse_file(file_path)
            if not result.success:
                return None
                
            analysis = self.analyzer.analyze_code(result.ast)
            if not analysis.success:
                return None
                
            return ModuleInfo(
                path=file_path,
                analysis=analysis
            )
            
        except Exception as e:
            raise ServiceError(f"File analysis failed: {e}") 