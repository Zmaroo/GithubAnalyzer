"""Analyzer service for code analysis"""
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass, field
from .configurable import ConfigurableService, ServiceConfig
from .base import ServiceError
from ..models.analysis import AnalysisResult
from ..models.module import ModuleInfo
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

@dataclass
class AnalyzerConfig(ServiceConfig):
    """Analyzer service configuration"""
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    supported_languages: List[str] = field(default_factory=lambda: ['python', 'javascript'])
    enable_deep_analysis: bool = True
    analysis_timeout: int = 300  # 5 minutes
    max_complexity: int = 100
    max_depth: int = 10

class AnalyzerError(ServiceError):
    """Error during code analysis"""
    pass

class AnalyzerService(ConfigurableService):
    """Service for code analysis"""
    
    def __init__(self, registry=None, config: Optional[AnalyzerConfig] = None):
        """Initialize analyzer service"""
        self.current_file = None
        self.context = None
        super().__init__(registry, config or AnalyzerConfig())
        
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize analyzer service"""
        try:
            if config:
                self._update_config(config)
                
            # Get required services
            self.parser = self.get_service('parser')
            if not self.parser:
                raise AnalyzerError("Parser service not available")
                
        except Exception as e:
            raise AnalyzerError(f"Failed to initialize analyzer: {e}")
            
    def analyze_file(self, file_path: str) -> Optional[ModuleInfo]:
        """Analyze a single file"""
        if not self.initialized:
            logger.error("Analyzer service not initialized")
            return None
            
        try:
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                return None
                
            # Check file size
            if Path(file_path).stat().st_size > self.service_config.max_file_size:
                logger.error(f"File too large: {file_path}")
                return None
                
            # Parse file
            with open(file_path, 'r') as f:
                content = f.read()
                
            parse_result = self.parser.parse_file(file_path, content)
            if not parse_result or not parse_result.get('success'):
                logger.error(f"Failed to parse {file_path}")
                return None
                
            # Calculate metrics
            metrics = self._calculate_metrics(parse_result['ast'])
            
            return ModuleInfo(
                path=file_path,
                ast=parse_result['ast'],
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze file {file_path}: {e}")
            return None
            
    def analyze_repository(self, repo_path: str) -> AnalysisResult:
        """Analyze entire repository"""
        if not self.initialized:
            return AnalysisResult(
                modules=[],
                errors=["Analyzer not initialized"],
                warnings=[],
                metrics={},
                success=False
            )
            
        try:
            if not Path(repo_path).is_dir():
                return AnalysisResult(
                    modules=[],
                    errors=[f"Invalid repository path: {repo_path}"],
                    warnings=[],
                    metrics={},
                    success=False
                )
                
            modules = []
            errors = []
            warnings = []
            
            # Analyze each file
            for root, _, files in Path(repo_path).rglob('*'):
                for file in files:
                    if file.suffix in ['.py', '.js']:  # Support both Python and JS
                        file_path = root / file
                        module_info = self.analyze_file(str(file_path))
                        if module_info:
                            modules.append(module_info)
                        else:
                            warnings.append(f"Failed to analyze {file_path}")

            if not modules:
                errors.append("No valid modules found")
                
            return AnalysisResult(
                modules=modules,
                errors=errors,
                warnings=warnings,
                metrics=self._aggregate_metrics(modules),
                success=len(modules) > 0
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
            
    def _calculate_metrics(self, ast: Any) -> Dict[str, Any]:
        """Calculate metrics for AST"""
        try:
            return {
                'complexity': self._calculate_complexity(ast),
                'depth': self._calculate_depth(ast),
                'lines': self._calculate_lines(ast)
            }
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            return {}
            
    def _cleanup(self) -> None:
        """Cleanup analyzer resources"""
        try:
            self.current_file = None
            self.context = None
        except Exception as e:
            logger.error(f"Failed to cleanup analyzer: {e}") 