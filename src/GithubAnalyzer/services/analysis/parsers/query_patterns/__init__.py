"""Query patterns package for tree-sitter parsers.

This package aggregates various modules:
  - templates: Templates for common query patterns and create pattern functions.
  - common: Common query patterns and optimization settings.
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

from .templates import PATTERN_TEMPLATES, create_function_pattern, create_class_pattern, create_method_pattern
from .common import COMMON_PATTERNS, DEFAULT_OPTIMIZATIONS, get_language_patterns
from .language_patterns import PYTHON_PATTERNS, C_PATTERNS, YAML_PATTERNS, JS_VARIANT_PATTERNS

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
    "JS_VARIANT_PATTERNS"
] 