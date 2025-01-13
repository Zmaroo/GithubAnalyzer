"""Analyzer service for code analysis"""
from typing import Optional, Dict, Any, List, TYPE_CHECKING
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
        
    def analyze_file(self, file_path: str) -> Optional[ModuleInfo]:
        """Analyze a single file"""
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
            logger.error(f"Failed to analyze file {file_path}: {e}")
            return None
            
    def analyze_repository(self, repo_path: str) -> AnalysisResult:
        """Analyze entire repository"""
        if not os.path.isdir(repo_path):
            return AnalysisResult(
                modules=[],
                errors=["Invalid repository path"],
                warnings=[],
                metrics={},
                success=False
            )

        try:
            modules = []
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        module_info = self.analyze_file(file_path)
                        if module_info:
                            modules.append(module_info)

            return AnalysisResult(
                modules=modules,
                errors=[],
                warnings=[],
                metrics=self._aggregate_metrics(modules),
                success=True
            )
        except Exception as e:
            logger.error(f"Failed to analyze repository: {e}")
            return AnalysisResult(
                modules=[],
                errors=[str(e)],
                warnings=[],
                metrics={},
                success=False
            )

    def _calculate_metrics(self, ast) -> Dict[str, Any]:
        """Calculate metrics for an AST"""
        try:
            return {
                'complexity': 0,
                'depth': 0,
                'lines': 0
            }
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            return {}

    def _aggregate_metrics(self, modules: List[ModuleInfo]) -> Dict[str, Any]:
        """Aggregate metrics across modules"""
        try:
            return {
                'total_complexity': sum(m.metrics.get('complexity', 0) for m in modules),
                'max_depth': max((m.metrics.get('depth', 0) for m in modules), default=0),
                'total_lines': sum(m.metrics.get('lines', 0) for m in modules)
            }
        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")
            return {}

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