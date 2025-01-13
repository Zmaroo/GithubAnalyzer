"""Framework detection service"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from .configurable import ConfigurableService, ServiceConfig
from .base import ServiceError
from ..models.module import ModuleInfo
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

@dataclass
class FrameworkConfig(ServiceConfig):
    """Framework detection configuration"""
    confidence_threshold: float = 0.7
    enable_deep_scan: bool = True
    scan_dependencies: bool = True
    framework_patterns: Dict[str, List[str]] = field(default_factory=lambda: {
        'django': ['django', 'rest_framework', 'django.db', 'django.urls'],
        'flask': ['flask', 'flask_restful', 'flask_sqlalchemy'],
        'fastapi': ['fastapi', 'pydantic'],
        'sqlalchemy': ['sqlalchemy', 'alembic'],
        'pydantic': ['pydantic', 'pydantic.base']
    })

class FrameworkError(ServiceError):
    """Error during framework detection"""
    pass

class FrameworkService(ConfigurableService):
    """Service for detecting frameworks used in code"""
    
    def __init__(self, registry=None, config: Optional[FrameworkConfig] = None):
        """Initialize framework detection service"""
        self.detected_frameworks = {}
        self.scan_results = {}
        super().__init__(registry, config or FrameworkConfig())
        
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize framework detection service"""
        try:
            if config:
                self._update_config(config)
                
            # Get required services
            self.analyzer = self.get_service('analyzer')
            if not self.analyzer:
                raise FrameworkError("Analyzer service not available")
                
        except Exception as e:
            raise FrameworkError(f"Failed to initialize framework detection: {e}")
            
    def detect_frameworks(self, module: ModuleInfo) -> Dict[str, float]:
        """Detect frameworks used in module"""
        if not self.initialized:
            logger.error("Framework service not initialized")
            return {}
            
        try:
            frameworks = {}
            for framework, patterns in self.service_config.framework_patterns.items():
                confidence = self._calculate_confidence(module, patterns)
                if confidence >= self.service_config.confidence_threshold:
                    frameworks[framework] = confidence
                    
            # Cache results
            self.detected_frameworks[module.path] = frameworks
            return frameworks
            
        except Exception as e:
            logger.error(f"Failed to detect frameworks: {e}")
            return {}
        
    def _calculate_confidence(self, module: ModuleInfo, patterns: List[str]) -> float:
        """Calculate confidence score for framework detection"""
        try:
            if not hasattr(module, 'imports') or not module.imports:
                return 0.0
                
            matches = sum(1 for pattern in patterns if any(
                pattern in imp for imp in module.imports
            ))
            
            # Weight the confidence score
            base_score = matches / len(patterns) if matches > 0 else 0.0
            
            if self.service_config.enable_deep_scan:
                # Add additional confidence from deep scan
                deep_score = self._deep_scan_confidence(module, patterns)
                return (base_score + deep_score) / 2
                
            return base_score
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence: {e}")
            return 0.0
            
    def _deep_scan_confidence(self, module: ModuleInfo, patterns: List[str]) -> float:
        """Perform deep scan for framework detection"""
        try:
            # Check for framework-specific patterns in code
            if not module.ast:
                return 0.0
                
            # Mock deep scan for now
            return 0.5
            
        except Exception as e:
            logger.error(f"Failed to perform deep scan: {e}")
            return 0.0
            
    def _cleanup(self) -> None:
        """Cleanup framework service resources"""
        try:
            self.detected_frameworks.clear()
            self.scan_results.clear()
        except Exception as e:
            logger.error(f"Failed to cleanup framework service: {e}") 