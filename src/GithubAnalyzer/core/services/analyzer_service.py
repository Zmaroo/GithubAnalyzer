"""Analyzer service for code analysis"""
from typing import Optional, Dict, Any, TYPE_CHECKING
from ..utils.logging import setup_logger
from .base import BaseService
from ..models.analysis import AnalysisResult
from ..models.module import ModuleInfo
import os

if TYPE_CHECKING:
    from ..registry import AnalysisToolRegistry

logger = setup_logger(__name__)

class AnalyzerService(BaseService):
    """Service for code analysis"""
    
    def __init__(self, registry: Optional['AnalysisToolRegistry'] = None):
        """Initialize analyzer service"""
        super().__init__(registry)
        self.current_file = None
        self.context = None
        self.initialized = True
        
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
            
    def analyze_single_file(self, file_path):
        if not os.path.exists(file_path):
            return None
            
        try:
            parser = self.registry.get_service('parser')
            parse_result = parser.parse_file(file_path)
            
            if parse_result.success:
                return ModuleInfo(
                    path=file_path,
                    ast=parse_result.ast,
                    metrics=self._calculate_metrics(parse_result.ast)
                )
            return None
        except Exception as e:
            return None

    def analyze_repository(self, repo_path):
        if not os.path.isdir(repo_path):
            return AnalysisResult(success=False)

        modules = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    module_info = self.analyze_single_file(file_path)
                    if module_info:
                        modules.append(module_info)

        return AnalysisResult(
            modules=modules,
            success=True
        ) 