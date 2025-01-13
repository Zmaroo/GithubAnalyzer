"""Common operations interface"""
from typing import List, Dict, Any, Optional
from .models import ModuleInfo, AnalysisResult
from .services import DatabaseService, ParserService

class CommonOperations:
    """Interface for common operations"""
    
    def __init__(self, registry):
        """Initialize with registry"""
        self.registry = registry
        
    @property
    def database_service(self) -> DatabaseService:
        """Get database service"""
        return self.registry.database_service
        
    @property
    def parser_service(self) -> ParserService:
        """Get parser service"""
        return self.registry.parser_service
        
    def analyze_file(self, file_path: str) -> Optional[ModuleInfo]:
        """Analyze a single file"""
        try:
            with open(file_path) as f:
                content = f.read()
            result = self.parser_service.parse_file(file_path, content)
            if not result.success:
                return None
            return ModuleInfo(
                path=file_path,
                success=True
            )
        except Exception:
            return None
            
    def analyze_repository(self, path: str) -> AnalysisResult:
        """Analyze entire repository"""
        return AnalysisResult(
            modules=[],
            success=True
        ) 