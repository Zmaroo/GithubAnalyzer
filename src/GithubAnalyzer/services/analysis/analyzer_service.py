"""Code analysis service"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .configurable import ConfigurableService, AnalyzerConfig
from .errors import AnalyzerError
from ..models.analysis import AnalysisResult, AnalysisContext
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

@dataclass
class AnalyzerMetrics:
    """Analyzer performance metrics"""
    files_analyzed: int = 0
    total_analysis_time: float = 0.0
    security_issues_found: int = 0
    type_errors_found: int = 0
    style_violations: int = 0
    complexity_violations: int = 0

class AnalyzerService(ConfigurableService):
    """Service for code analysis"""
    
    def __init__(self, registry=None, config: Optional[AnalyzerConfig] = None):
        self.parser_service = None
        self.graph_service = None
        self.metrics = AnalyzerMetrics()
        super().__init__(registry, config or AnalyzerConfig())
        
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize analyzer service"""
        try:
            if config:
                self._update_config(config)
                
            # Get required services as per cursorrules
            self.parser_service = self.registry.get_service('parser')
            self.graph_service = self.registry.get_service('graph')
            
            if not self.parser_service or not self.graph_service:
                raise AnalyzerError("Required services not available")
                
            # Initialize analysis components based on config
            if self.service_config.enable_type_checking:
                self._init_type_checker()
                
            if self.service_config.enable_security_checks:
                self._init_security_analyzer()
                
            if self.service_config.enable_style_checks:
                self._init_style_checker()
                
        except Exception as e:
            raise AnalyzerError(f"Failed to initialize analyzer service: {e}")

    def _validate_requirements(self) -> bool:
        """Validate service requirements from cursorrules"""
        if not super()._validate_requirements():
            return False
            
        config = self.service_config
        
        # Check required services
        if not self.parser_service or not self.graph_service:
            logger.error("Required services not available")
            return False
            
        # Check analysis requirements
        if config.enable_type_checking and not hasattr(self, '_type_checker'):
            logger.error("Type checking enabled but not initialized")
            return False
            
        if config.enable_security_checks and not hasattr(self, '_security_analyzer'):
            logger.error("Security checks enabled but not initialized")
            return False
            
        return True

    def analyze_code(self, context: AnalysisContext) -> AnalysisResult:
        """Analyze code with full context"""
        try:
            # Parse code using parser service
            parse_result = self.parser_service.parse_file(
                context.current_file,
                context.content
            )
            
            if not parse_result.success:
                return AnalysisResult(
                    modules=[],
                    success=False,
                    errors=parse_result.errors
                )
                
            # Run enabled analysis
            analysis_results = []
            
            if self.service_config.enable_type_checking:
                type_check_result = self._run_type_checking(parse_result.ast)
                analysis_results.append(type_check_result)
                
            if self.service_config.enable_security_checks:
                security_result = self._run_security_analysis(parse_result.ast)
                analysis_results.append(security_result)
                
            if self.service_config.enable_style_checks:
                style_result = self._run_style_analysis(parse_result.ast)
                analysis_results.append(style_result)
                
            # Run graph analysis
            graph_result = self.graph_service.analyze_code_structure(parse_result.ast)
            
            # Update metrics
            self.metrics.files_analyzed += 1
            
            return AnalysisResult(
                modules=analysis_results,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return AnalysisResult(
                modules=[],
                success=False,
                errors=[str(e)]
            )

    def _init_type_checker(self) -> None:
        """Initialize type checking system"""
        try:
            # Initialize type checker based on config
            logger.info("Initializing type checker")
            self._type_checker = {}  # Replace with actual type checker
        except Exception as e:
            raise AnalyzerError(f"Failed to initialize type checker: {e}")

    def _init_security_analyzer(self) -> None:
        """Initialize security analyzer"""
        try:
            # Initialize security analyzer based on config
            logger.info("Initializing security analyzer")
            self._security_analyzer = {}  # Replace with actual security analyzer
        except Exception as e:
            raise AnalyzerError(f"Failed to initialize security analyzer: {e}")

    def _init_style_checker(self) -> None:
        """Initialize style checker"""
        try:
            # Initialize style checker based on config
            logger.info("Initializing style checker")
            self._style_checker = {}  # Replace with actual style checker
        except Exception as e:
            raise AnalyzerError(f"Failed to initialize style checker: {e}")

    def _cleanup(self) -> None:
        """Cleanup analyzer resources"""
        try:
            self.parser_service = None
            self.graph_service = None
        except Exception as e:
            logger.error(f"Failed to cleanup analyzer resources: {e}")

    def get_metrics(self) -> AnalyzerMetrics:
        """Get analyzer metrics"""
        return self.metrics

    # ... additional analysis methods ... 