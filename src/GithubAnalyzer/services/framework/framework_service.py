"""Framework detection and analysis service"""
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from pathlib import Path
from .configurable import ConfigurableService, FrameworkConfig
from .errors import FrameworkError
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

@dataclass
class FrameworkMetrics:
    """Framework detection metrics"""
    frameworks_detected: int = 0
    dependencies_scanned: int = 0
    confidence_scores: Dict[str, float] = None
    scan_time: float = 0.0
    cache_hits: int = 0

    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = {}

class FrameworkService(ConfigurableService):
    """Service for framework detection and analysis"""
    
    def __init__(self, registry=None, config: Optional[FrameworkConfig] = None):
        self.analyzer_service = None
        self.metrics = FrameworkMetrics()
        self._framework_cache: Dict[str, Dict[str, Any]] = {}
        super().__init__(registry, config or FrameworkConfig())
        
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize framework service"""
        try:
            if config:
                self._update_config(config)
                
            # Get analyzer service as required by cursorrules
            self.analyzer_service = self.registry.get_service('analyzer')
            if not self.analyzer_service:
                raise FrameworkError("Required analyzer service not available")
                
            # Initialize framework patterns
            self._init_framework_patterns()
                
        except Exception as e:
            raise FrameworkError(f"Failed to initialize framework service: {e}")

    def _init_framework_patterns(self) -> None:
        """Initialize framework detection patterns"""
        try:
            self.patterns = self.service_config.framework_patterns
            if not self.patterns:
                raise FrameworkError("No framework patterns configured")
        except Exception as e:
            raise FrameworkError(f"Failed to initialize framework patterns: {e}")

    def _validate_requirements(self) -> bool:
        """Validate service requirements from cursorrules"""
        if not super()._validate_requirements():
            return False
            
        config = self.service_config
        
        # Check analyzer service
        if not self.analyzer_service:
            logger.error("Required analyzer service not available")
            return False
            
        # Check confidence threshold
        if not 0 <= config.confidence_threshold <= 1:
            logger.error("Invalid confidence threshold")
            return False
            
        # Check framework patterns
        if not config.framework_patterns:
            logger.error("No framework patterns configured")
            return False
            
        return True

    def detect_frameworks(self, repo_path: str) -> Dict[str, Any]:
        """Detect frameworks in repository"""
        try:
            if not self.initialized:
                raise FrameworkError("Service not initialized")
                
            results = {
                'frameworks': [],
                'dependencies': [],
                'confidence_scores': {}
            }
            
            # Check cache first
            cache_key = str(Path(repo_path).resolve())
            if cache_key in self._framework_cache:
                self.metrics.cache_hits += 1
                return self._framework_cache[cache_key]
            
            # Scan for framework patterns
            detected_patterns = self._scan_for_patterns(repo_path)
            
            # Analyze dependencies if enabled
            if self.service_config.scan_dependencies:
                dependencies = self._analyze_dependencies(repo_path)
                results['dependencies'] = dependencies
            
            # Calculate confidence scores
            for framework, patterns in detected_patterns.items():
                confidence = self._calculate_confidence(patterns)
                if confidence >= self.service_config.confidence_threshold:
                    results['frameworks'].append(framework)
                    results['confidence_scores'][framework] = confidence
            
            # Cache results
            self._framework_cache[cache_key] = results
            
            # Update metrics
            self.metrics.frameworks_detected = len(results['frameworks'])
            
            return results
            
        except Exception as e:
            logger.error(f"Framework detection failed: {e}")
            return {
                'frameworks': [],
                'dependencies': [],
                'confidence_scores': {}
            }

    def _scan_for_patterns(self, repo_path: str) -> Dict[str, Set[str]]:
        """Scan repository for framework patterns"""
        try:
            detected_patterns: Dict[str, Set[str]] = {}
            
            for framework, patterns in self.patterns.items():
                detected_patterns[framework] = set()
                for pattern in patterns:
                    if self._check_pattern(repo_path, pattern):
                        detected_patterns[framework].add(pattern)
                        
            return detected_patterns
            
        except Exception as e:
            logger.error(f"Pattern scanning failed: {e}")
            return {}

    def _analyze_dependencies(self, repo_path: str) -> List[Dict[str, Any]]:
        """Analyze project dependencies"""
        try:
            dependencies = []
            
            # Check common dependency files
            dep_files = ['requirements.txt', 'package.json', 'Gemfile']
            for dep_file in dep_files:
                file_path = Path(repo_path) / dep_file
                if file_path.exists():
                    deps = self._parse_dependency_file(file_path)
                    dependencies.extend(deps)
                    
            self.metrics.dependencies_scanned = len(dependencies)
            return dependencies
            
        except Exception as e:
            logger.error(f"Dependency analysis failed: {e}")
            return []

    def _calculate_confidence(self, detected_patterns: Set[str]) -> float:
        """Calculate confidence score for framework detection"""
        try:
            if not detected_patterns:
                return 0.0
                
            # Calculate based on number of patterns matched
            total_patterns = len(self.patterns.get(next(iter(detected_patterns)), []))
            if total_patterns == 0:
                return 0.0
                
            return len(detected_patterns) / total_patterns
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.0

    def _cleanup(self) -> None:
        """Cleanup framework service resources"""
        try:
            self.analyzer_service = None
            self._framework_cache.clear()
            self.patterns = {}
        except Exception as e:
            logger.error(f"Failed to cleanup framework service: {e}")

    def get_metrics(self) -> FrameworkMetrics:
        """Get framework detection metrics"""
        return self.metrics 