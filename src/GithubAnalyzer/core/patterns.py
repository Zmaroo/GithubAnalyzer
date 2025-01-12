from typing import Dict, Any, List, Optional
import logging
import os
import ast
from .code_analyzer import CodeAnalyzer
from .utils import setup_logger

logger = setup_logger(__name__)

class PatternDetector:
    """Centralized pattern detection functionality"""
    
    @staticmethod
    def detect_all(parse_result: Dict[str, Any], file_path: Optional[str] = None) -> Dict[str, List[str]]:
        """Detect all patterns in code"""
        return {
            'structural': PatternDetector.detect_structural_patterns(parse_result),
            'design': PatternDetector.detect_design_patterns(parse_result),
            'usage': PatternDetector.detect_usage_patterns(parse_result),
            'architectural': PatternDetector.detect_architectural_patterns(parse_result),
            'framework': PatternDetector.detect_frameworks(parse_result.get('imports', [])),
            'style': PatternDetector.detect_style_patterns(file_path) if file_path else []
        }

    @staticmethod
    def detect_frameworks(imports: List[str]) -> List[str]:
        """Detect frameworks from imports"""
        frameworks = []
        framework_patterns = {
            'django': ['django'],
            'flask': ['flask'],
            'fastapi': ['fastapi'],
            'pytorch': ['torch'],
            'tensorflow': ['tensorflow', 'tf'],
            'numpy': ['numpy', 'np'],
            'pandas': ['pandas', 'pd']
        }
        return [framework for framework, patterns in framework_patterns.items() 
                if any(pattern in imp.lower() for pattern in patterns)
                for imp in imports]

    @staticmethod
    def detect_structural_patterns(parse_result: Dict[str, Any]) -> List[str]:
        """Detect structural code patterns"""
        patterns = []
        semantic = parse_result["semantic"]

        # Object-Oriented patterns
        if len(semantic.get("classes", [])) > 0:
            patterns.append('object_oriented')
            
            # Check inheritance patterns
            if any(len(cls.get("bases", [])) > 0 for cls in semantic["classes"]):
                patterns.append('inheritance_based')

        # Functional patterns
        if any(PatternDetector._is_functional(func) for func in semantic.get("functions", [])):
            patterns.append('functional')

        # Async patterns
        if any('async' in f["text"] for f in semantic.get("functions", [])):
            patterns.append('asynchronous')

        # Module patterns
        if len(semantic.get("imports", [])) > 10:
            patterns.append('highly_modular')

        return patterns

    @staticmethod
    def detect_design_patterns(parse_result: Dict[str, Any]) -> List[str]:
        """Detect common design patterns"""
        patterns = []
        semantic = parse_result["semantic"]

        for cls in semantic.get("classes", []):
            # Creational patterns
            if cls["text"].endswith('Factory'):
                patterns.append('factory')
            elif cls["text"].endswith('Builder'):
                patterns.append('builder')
            elif 'Singleton' in cls.get("bases", []):
                patterns.append('singleton')

            # Structural patterns
            elif cls["text"].endswith('Adapter'):
                patterns.append('adapter')
            elif cls["text"].endswith('Decorator'):
                patterns.append('decorator')
            elif 'Proxy' in cls["text"]:
                patterns.append('proxy')

            # Behavioral patterns
            elif cls["text"].endswith('Observer'):
                patterns.append('observer')
            elif cls["text"].endswith('Strategy'):
                patterns.append('strategy')
            elif 'Command' in cls["text"]:
                patterns.append('command')

        return patterns

    @staticmethod
    def detect_usage_patterns(parse_result: Dict[str, Any]) -> List[str]:
        """Detect code usage patterns"""
        patterns = []
        semantic = parse_result["semantic"]

        # Context manager usage
        if any('__enter__' in f["text"] for f in semantic.get("functions", [])):
            patterns.append('context_manager')

        # Comprehension patterns
        if parse_result["root_node"].text.count('[') > 5:  # Heuristic for list comprehensions
            patterns.append('list_comprehensions')

        # Decorator usage
        if any('@' in f["text"] for f in semantic.get("functions", [])):
            patterns.append('decorators')

        # Generator usage
        if any('yield' in f["text"] for f in semantic.get("functions", [])):
            patterns.append('generators')

        return patterns

    @staticmethod
    def detect_architectural_patterns(parse_result: Dict[str, Any]) -> List[str]:
        """Detect architectural patterns"""
        patterns = []
        semantic = parse_result["semantic"]

        # MVC pattern
        if any('Model' in cls["text"] for cls in semantic.get("classes", [])) and \
           any('View' in cls["text"] for cls in semantic.get("classes", [])):
            patterns.append('mvc')

        # Repository pattern
        if any('Repository' in cls["text"] for cls in semantic.get("classes", [])):
            patterns.append('repository')

        # Service layer
        if any('Service' in cls["text"] for cls in semantic.get("classes", [])):
            patterns.append('service_layer')

        # Dependency injection
        if any('__init__' in f["text"] and len(f.get("params", [])) > 2 
               for f in semantic.get("functions", [])):
            patterns.append('dependency_injection')

        return patterns

    @staticmethod
    def detect_style_patterns(file_path: str) -> List[str]:
        """Detect coding style patterns"""
        patterns = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check naming conventions
            if '_' in content:
                patterns.append('snake_case')
            if any(c.isupper() for c in content):
                patterns.append('PascalCase')
                
            # Check docstring style
            if '"""' in content:
                patterns.append('docstring_double')
            elif "'''" in content:
                patterns.append('docstring_single')
                
            # Check import style
            if 'from typing import' in content:
                patterns.append('type_hints')
                
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting style patterns: {e}")
            return patterns

    @staticmethod
    def detect_code_smells(parse_result: Dict[str, Any]) -> List[str]:
        """Detect potential code smells"""
        smells = []
        semantic = parse_result["semantic"]

        # Long methods
        for func in semantic.get("functions", []):
            if func.get("end_point", (0,))[0] - func.get("start_point", (0,))[0] > 50:
                smells.append(f'long_method:{func["text"]}')

        # God classes
        for cls in semantic.get("classes", []):
            if len(cls.get("methods", [])) > 20:
                smells.append(f'god_class:{cls["text"]}')

        # Complex conditionals
        if parse_result["root_node"].text.count('if') > 10:
            smells.append('complex_conditionals')

        return smells

    @staticmethod
    def _is_functional(func: Dict[str, Any]) -> bool:
        """Check if a function follows functional programming patterns"""
        return all([
            not func.get("mutates_state", False),
            not func.get("has_side_effects", False),
            len(func.get("returns", [])) > 0
        ]) 