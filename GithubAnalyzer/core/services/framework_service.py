from typing import Dict, Any
from .base_service import BaseService
from ..parsers.base import ParseResult

class FrameworkService(BaseService):
    """Service for framework detection and analysis"""
    
    def _initialize(self) -> None:
        self.analyzers = {
            'pydantic': PydanticAnalyzer(),
            'fastapi': FastAPIAnalyzer(),
            'django': DjangoAnalyzer(),
            # Add other framework analyzers
        }
    
    def analyze_file(self, file_path: str, parse_result: ParseResult) -> Dict[str, Any]:
        """Analyze file for framework usage"""
        results = {}
        for name, analyzer in self.analyzers.items():
            framework_info = analyzer.analyze(file_path, parse_result)
            if framework_info:
                results[name] = framework_info
        return results 