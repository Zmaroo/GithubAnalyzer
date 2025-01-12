from typing import Dict, Any, List, Optional
from .base_service import BaseService
from ..models.code import ModuleInfo
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class FrameworkService(BaseService):
    """Service for framework detection and analysis"""
    
    def _initialize(self) -> None:
        self.framework_patterns = {
            'django': {
                'imports': ['django'],
                'files': ['manage.py', 'wsgi.py', 'asgi.py'],
                'patterns': ['urlpatterns', 'INSTALLED_APPS']
            },
            'flask': {
                'imports': ['flask'],
                'patterns': ['app = Flask', 'route(']
            },
            'fastapi': {
                'imports': ['fastapi'],
                'patterns': ['app = FastAPI', '@app.']
            },
            'pytorch': {
                'imports': ['torch'],
                'patterns': ['nn.Module', 'torch.nn']
            },
            'tensorflow': {
                'imports': ['tensorflow', 'tf'],
                'patterns': ['tf.keras', 'model.fit']
            },
            'sqlalchemy': {
                'imports': ['sqlalchemy'],
                'patterns': ['Base = declarative_base()', 'Column(']
            },
            'pydantic': {
                'imports': ['pydantic'],
                'patterns': ['BaseModel', 'Field(']
            }
        }

    def detect_frameworks(self, module: ModuleInfo) -> Dict[str, float]:
        """Detect frameworks used in a module with confidence scores"""
        try:
            results = {}
            
            for framework, patterns in self.framework_patterns.items():
                confidence = self._calculate_framework_confidence(module, patterns)
                if confidence > 0:
                    results[framework] = confidence
                    
            return results
        except Exception as e:
            logger.error(f"Error detecting frameworks: {e}")
            return {}

    def _calculate_framework_confidence(self, module: ModuleInfo, patterns: Dict[str, List[str]]) -> float:
        """Calculate confidence score for framework detection"""
        try:
            score = 0.0
            total_checks = 0
            
            # Check imports
            if any(imp in module.imports for imp in patterns['imports']):
                score += 1.0
            total_checks += 1
            
            # Check file patterns
            if 'files' in patterns:
                if any(pattern in module.path for pattern in patterns['files']):
                    score += 1.0
                total_checks += 1
            
            # Check code patterns
            if 'patterns' in patterns:
                pattern_matches = sum(
                    1 for pattern in patterns['patterns']
                    if self._check_pattern_in_module(module, pattern)
                )
                if pattern_matches:
                    score += pattern_matches / len(patterns['patterns'])
                total_checks += 1
                
            return score / total_checks if total_checks > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating framework confidence: {e}")
            return 0.0

    def _check_pattern_in_module(self, module: ModuleInfo, pattern: str) -> bool:
        """Check if pattern exists in module code"""
        try:
            # Check function definitions
            for func in module.functions:
                if pattern in func.name or (func.docstring and pattern in func.docstring):
                    return True
                    
            # Check class definitions
            for cls in module.classes:
                if pattern in cls.name or (cls.docstring and pattern in cls.docstring):
                    return True
                for method in cls.methods:
                    if pattern in method.name or (method.docstring and pattern in method.docstring):
                        return True
                        
            return False
        except Exception as e:
            logger.error(f"Error checking pattern: {e}")
            return False 