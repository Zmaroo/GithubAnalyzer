"""Analysis models for the GithubAnalyzer package."""

# Code analysis models
# AST models
from GithubAnalyzer.models.core.ast import (NodeDict, NodeList, TreeSitterEdit,
                                            TreeSitterRange)

from .code_analysis import (AnalysisConfig, BatchAnalysisResult,
                            CodeAnalysisResult, CodeMetrics)
# Language analysis models
from .language import (CodeAnalysis, LanguageDetectionResult,
                       LanguageIndicator, LanguagePattern)
# Pattern models
from .pattern_registry import (PATTERN_REGISTRY, get_language_patterns,
                               get_optimization_settings, get_query_pattern)
# Query models
from .query import (QueryCapture, QueryExecutor, QueryOptimizationSettings,
                    QueryPattern, QueryResult, QueryStats)
from .query_constants import (PATTERN_CATEGORY_CLASS, PATTERN_CATEGORY_COMMENT,
                              PATTERN_CATEGORY_CONTROL_FLOW,
                              PATTERN_CATEGORY_ERROR,
                              PATTERN_CATEGORY_FUNCTION,
                              PATTERN_CATEGORY_IMPORT,
                              PATTERN_CATEGORY_INTERFACE,
                              PATTERN_CATEGORY_METHOD,
                              PATTERN_CATEGORY_NAMESPACE,
                              PATTERN_CATEGORY_STRING, PATTERN_CATEGORY_STRUCT,
                              PATTERN_TYPE_CLASS, PATTERN_TYPE_COMMON,
                              PATTERN_TYPE_CONTROL_FLOW, PATTERN_TYPE_FUNCTION,
                              PATTERN_TYPE_INTERFACE, PATTERN_TYPE_JS_TS,
                              PATTERN_TYPE_LANGUAGE_SPECIFIC,
                              PATTERN_TYPE_QUERY)
# Result models
from .results import (AnalysisMetrics, AnalysisResult, BaseAnalysisResult,
                      BaseMetrics)
# Tree-sitter models
from .tree_sitter import (TreeSitterEdit, TreeSitterQueryMatch,
                          TreeSitterQueryResult, TreeSitterResult)
# Type definitions
from .types import (AnalysisType, MetricsType, PatternType, QueryType,
                    ResultType, StatsType)

# Constants
CAPTURE_TYPES = {
    'identifier': 'identifier',
    'name': 'name',
    'type': 'type',
    'value': 'value',
    'body': 'body',
    'parameters': 'parameters',
    'return_type': 'return_type',
    'comment': 'comment',
    'string': 'string',
    'error': 'error'
}

OPTIMIZATION_LEVELS = {
    'none': 0,
    'basic': 1,
    'aggressive': 2
}

PATTERN_TYPES = {
    'query': PATTERN_TYPE_QUERY,
    'common': PATTERN_TYPE_COMMON,
    'interface': PATTERN_TYPE_INTERFACE,
    'function': PATTERN_TYPE_FUNCTION,
    'class': PATTERN_TYPE_CLASS,
    'control_flow': PATTERN_TYPE_CONTROL_FLOW,
    'js_ts': PATTERN_TYPE_JS_TS,
    'language_specific': PATTERN_TYPE_LANGUAGE_SPECIFIC
}

QUERY_TYPES = {
    'semantic': 'semantic',
    'structural': 'structural',
    'hybrid': 'hybrid'
}

__all__ = [
    # Code analysis
    'AnalysisConfig', 'CodeAnalysisResult',
    'CodeMetrics', 'BatchAnalysisResult',
    
    # AST models
    'TreeSitterEdit', 'TreeSitterRange',
    'NodeDict', 'NodeList',
    
    # Language analysis
    'LanguageDetectionResult', 'LanguagePattern',
    'LanguageIndicator', 'CodeAnalysis',
    
    # Pattern registry
    'PATTERN_REGISTRY', 'get_query_pattern',
    'get_language_patterns', 'get_optimization_settings',
    
    # Query models
    'QueryCapture', 'QueryPattern', 'QueryResult',
    'QueryStats', 'QueryExecutor', 'QueryOptimizationSettings',
    
    # Pattern types
    'PATTERN_TYPE_QUERY', 'PATTERN_TYPE_COMMON',
    'PATTERN_TYPE_INTERFACE', 'PATTERN_TYPE_FUNCTION',
    'PATTERN_TYPE_CLASS', 'PATTERN_TYPE_CONTROL_FLOW',
    'PATTERN_TYPE_JS_TS', 'PATTERN_TYPE_LANGUAGE_SPECIFIC',
    
    # Pattern categories
    'PATTERN_CATEGORY_CLASS', 'PATTERN_CATEGORY_COMMENT',
    'PATTERN_CATEGORY_CONTROL_FLOW', 'PATTERN_CATEGORY_ERROR',
    'PATTERN_CATEGORY_FUNCTION', 'PATTERN_CATEGORY_IMPORT',
    'PATTERN_CATEGORY_INTERFACE', 'PATTERN_CATEGORY_METHOD',
    'PATTERN_CATEGORY_NAMESPACE', 'PATTERN_CATEGORY_STRING',
    'PATTERN_CATEGORY_STRUCT',
    
    # Result models
    'AnalysisMetrics', 'AnalysisResult',
    'BaseAnalysisResult', 'BaseMetrics',
    
    # Tree-sitter models
    'TreeSitterEdit', 'TreeSitterQueryMatch',
    'TreeSitterQueryResult', 'TreeSitterResult',
    
    # Type definitions
    'AnalysisType', 'MetricsType', 'PatternType',
    'QueryType', 'ResultType', 'StatsType',
    
    # Constants
    'CAPTURE_TYPES', 'OPTIMIZATION_LEVELS',
    'PATTERN_TYPES', 'QUERY_TYPES'
] 
