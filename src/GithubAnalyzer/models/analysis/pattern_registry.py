"""Registry for tree-sitter query patterns."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from GithubAnalyzer.models.core.ast import TreeSitterBase
from GithubAnalyzer.models.core.base_model import BaseModel
from GithubAnalyzer.models.core.language import (is_js_variant,
                                                 supports_classes,
                                                 supports_interfaces)
from GithubAnalyzer.services.analysis.parsers.patterns import (
    LANGUAGE_PATTERNS,
    JS_TS_PATTERNS
)
from GithubAnalyzer.services.analysis.parsers.patterns.languages.common import (
    JS_TS_SHARED_PATTERNS
)
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

# Pattern types
PATTERN_TYPE_COMMON = "common"
PATTERN_TYPE_INTERFACE = "interface"
PATTERN_TYPE_FUNCTION = "function"
PATTERN_TYPE_CLASS = "class"
PATTERN_TYPE_METHOD = "method"
PATTERN_TYPE_CONTROL_FLOW = "control_flow"
PATTERN_TYPE_JS_TS = "js_ts"
PATTERN_TYPE_LANGUAGE_SPECIFIC = "language_specific"

@dataclass
class PatternRegistry(BaseModel):
    """Registry for tree-sitter query patterns."""
    _patterns: Dict[str, Dict[str, str]] = field(default_factory=dict)
    _language_patterns: Dict[str, Dict[str, str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize pattern registry."""
        self._initialize_patterns()
        
    def _initialize_patterns(self):
        """Initialize all pattern types."""
        self._initialize_language_specific_patterns()
        self._initialize_js_ts_patterns()
        
    def _initialize_js_ts_patterns(self):
        """Initialize JavaScript/TypeScript patterns."""
        self._patterns[PATTERN_TYPE_JS_TS] = JS_TS_SHARED_PATTERNS
        self._log("debug", "Initialized JS/TS patterns",
                pattern_count=len(JS_TS_SHARED_PATTERNS))

    def _initialize_language_specific_patterns(self):
        """Initialize language-specific patterns."""
        # Add all language-specific patterns from the new structure
        self._language_patterns.update(LANGUAGE_PATTERNS)
        self._log("debug", "Initialized language-specific patterns",
                pattern_count=len(self._language_patterns))
        
    def get_pattern(self, pattern_type: str, pattern_name: str, language: Optional[str] = None) -> Optional[str]:
        """Get a query pattern by type and name."""
        if pattern_type == PATTERN_TYPE_LANGUAGE_SPECIFIC and language:
            return self._get_language_pattern(language, pattern_name)
            
        if pattern_type in self._patterns and pattern_name in self._patterns[pattern_type]:
            pattern = self._patterns[pattern_type][pattern_name]
            self._log("debug", "Retrieved pattern", 
                    pattern_type=pattern_type,
                    pattern_name=pattern_name,
                    language=language)
            return pattern
            
        self._log("warning", "Pattern not found",
                pattern_type=pattern_type,
                pattern_name=pattern_name,
                language=language)
        return None
        
    def get_language_patterns(self, language: str) -> Dict[str, str]:
        """Get all patterns for a specific language."""
        patterns = {}
        
        # Add JS/TS patterns if applicable
        if is_js_variant(language):
            patterns.update(JS_TS_SHARED_PATTERNS)
            
        # Add language-specific patterns
        if language in self._language_patterns:
            patterns.update(self._language_patterns[language])
            
        self._log("debug", "Retrieved language patterns",
                language=language,
                pattern_count=len(patterns))
        return patterns
        
    def register_language_pattern(self, language: str, pattern_name: str, pattern: str):
        """Register a language-specific pattern."""
        if language not in self._language_patterns:
            self._language_patterns[language] = {}
            
        self._language_patterns[language][pattern_name] = pattern
        self._log("debug", "Registered language pattern",
                language=language,
                pattern_name=pattern_name)
        
    def _get_language_pattern(self, language: str, pattern_name: str) -> Optional[str]:
        """Get a language-specific pattern."""
        if language in self._language_patterns and pattern_name in self._language_patterns[language]:
            return self._language_patterns[language][pattern_name]
        return None

# Global pattern registry instance
PATTERN_REGISTRY = PatternRegistry()

def get_query_pattern(language: str, pattern_name: str) -> Optional[str]:
    """Get a query pattern for a language."""
    return PATTERN_REGISTRY.get_pattern(PATTERN_TYPE_LANGUAGE_SPECIFIC, pattern_name, language)

def get_language_patterns(language: str) -> Dict[str, str]:
    """Get all patterns for a language."""
    return PATTERN_REGISTRY.get_language_patterns(language)

def get_optimization_settings(language: str) -> Dict[str, Any]:
    """Get optimization settings for a language."""
    return {} # Default empty settings since we removed the old config structure 