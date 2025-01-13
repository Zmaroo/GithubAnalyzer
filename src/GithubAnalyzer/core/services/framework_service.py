"""Framework detection service"""
from typing import Dict, Any, Optional
from .base import BaseService
from ..models.module import ModuleInfo
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class FrameworkService(BaseService):
    """Service for detecting frameworks used in code"""
    
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize framework detection service"""
        self.framework_patterns = {
            'django': ['django', 'rest_framework'],
            'flask': ['flask', 'flask_restful'],
            'fastapi': ['fastapi'],
            'sqlalchemy': ['sqlalchemy'],
            'pydantic': ['pydantic']
        }
        self.initialized = True
        
    def shutdown(self) -> bool:
        """Cleanup resources"""
        try:
            self.initialized = False
            return True
        except Exception as e:
            logger.error(f"Failed to shutdown framework service: {e}")
            return False
            
    def detect_frameworks(self, module: ModuleInfo) -> Dict[str, float]:
        """Detect frameworks used in module"""
        frameworks = {}
        
        for framework, patterns in self.framework_patterns.items():
            confidence = self._calculate_confidence(module, patterns)
            if confidence > 0:
                frameworks[framework] = confidence
                
        return frameworks
        
    def _calculate_confidence(self, module: ModuleInfo, patterns: list) -> float:
        """Calculate confidence score for framework detection"""
        matches = sum(1 for pattern in patterns if any(
            pattern in imp for imp in module.imports
        ))
        return matches / len(patterns) if matches > 0 else 0.0 