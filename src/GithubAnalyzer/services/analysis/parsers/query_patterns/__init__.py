"""Query patterns package for tree-sitter parsers.

This package aggregates various modules:
  - templates: Templates for common query patterns and create pattern functions.
  - base_query_patterns: Common query patterns, optimization settings, and language mappings.
  - language_patterns: Language-specific hard-coded query patterns.

Exports:
  PATTERN_TEMPLATES,
  create_function_pattern,
  create_class_pattern,
  create_method_pattern,
  COMMON_PATTERNS,
  DEFAULT_OPTIMIZATIONS,
  get_language_patterns,
  PYTHON_PATTERNS,
  C_PATTERNS,
  YAML_PATTERNS,
  JS_VARIANT_PATTERNS
"""

from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

from .base_query_patterns import (COMMON_PATTERNS, DEFAULT_OPTIMIZATIONS,
                                  EXTENSION_TO_LANGUAGE, QUERY_PATTERNS,
                                  SPECIAL_FILENAMES, QueryOptimizationSettings,
                                  get_language_patterns,
                                  get_optimization_settings, get_query_pattern)
from .language_patterns import (C_PATTERNS, JS_VARIANT_PATTERNS,
                                PYTHON_PATTERNS, YAML_PATTERNS)
from .templates import (PATTERN_TEMPLATES, create_class_pattern,
                        create_function_pattern, create_method_pattern)

logger.debug("Query patterns package initialized", extra={
    'context': {
        'operation': 'initialization',
        'component': 'query_patterns',
        'available_languages': list(QUERY_PATTERNS.keys()),
        'pattern_types': list(COMMON_PATTERNS.keys())
    }
})

__all__ = [
    "PATTERN_TEMPLATES",
    "create_function_pattern",
    "create_class_pattern",
    "create_method_pattern",
    "COMMON_PATTERNS",
    "DEFAULT_OPTIMIZATIONS",
    "get_language_patterns",
    "PYTHON_PATTERNS",
    "C_PATTERNS",
    "YAML_PATTERNS",
    "JS_VARIANT_PATTERNS",
    "QUERY_PATTERNS",
    "EXTENSION_TO_LANGUAGE",
    "SPECIAL_FILENAMES",
    "QueryOptimizationSettings",
    "get_optimization_settings",
    "get_query_pattern"
] 