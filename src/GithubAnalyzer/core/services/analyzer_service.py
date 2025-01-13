"""Analyzer service for code analysis"""
from typing import Optional, Dict, Any
from .base import BaseService
from ..models.analysis import AnalysisResult
from ..models.module import ModuleInfo
from ..utils.logging import setup_logger
import os

logger = setup_logger(__name__)

class AnalyzerService(BaseService):
    """Service for code analysis"""
    
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize analyzer service"""
        self.current_file = None
        self.context = None
        self.initialized = True
        
    def shutdown(self) -> bool:
        """Cleanup resources"""
        try:
            self.current_file = None
            self.context = None
            self.initialized = False
            return True
        except Exception as e:
            logger.error(f"Failed to shutdown analyzer: {e}")
            return False
            
    def analyze_repository(self, path: str) -> Optional[AnalysisResult]:
        """Analyze entire repository"""
        try:
            if not path or not os.path.exists(path):
                return AnalysisResult(
                    modules=[],
                    errors=["Invalid repository path"],
                    success=False
                )
            
            modules = []
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        module_info = self.analyze_file(file_path)
                        if module_info:
                            modules.append(module_info)
                        
            return AnalysisResult(
                modules=modules,
                success=True
            )
        except Exception as e:
            logger.error(f"Failed to analyze repository: {e}")
            return AnalysisResult(
                modules=[],
                errors=[str(e)],
                success=False
            )
            
    def analyze_file(self, file_path: str) -> Optional[ModuleInfo]:
        """Analyze single file"""
        try:
            if not os.path.exists(file_path):
                return None
            
            with open(file_path) as f:
                content = f.read()
            
            # Parse file content
            parse_result = self.registry.parser_service.parse_file(file_path, content)
            if not parse_result.success:
                return None
            
            # Extract module info
            return ModuleInfo(
                path=file_path,
                imports=parse_result.semantic.get('imports', []),
                functions=parse_result.semantic.get('functions', []),
                classes=parse_result.semantic.get('classes', []),
                success=True
            )
        except Exception as e:
            logger.error(f"Failed to analyze file {file_path}: {e}")
            return None 