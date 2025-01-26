from typing import Dict, Optional, Any, Tuple, Union
"""Query patterns for tree-sitter.

Contains predefined patterns for common code elements and their optimization settings.
"""
from dataclasses import dataclass

@dataclass
class QueryOptimizationSettings:
    """Settings for optimizing query execution."""
    match_limit: Optional[int] = None  # Maximum number of in-progress matches
    max_start_depth: Optional[int] = None  # Maximum start depth for query
    timeout_micros: Optional[int] = None  # Maximum duration in microseconds
    byte_range: Optional[Tuple[int, int]] = None  # Limit query to byte range
    point_range: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None  # Limit query to point range

# Query patterns by language with assertions and settings
QUERY_PATTERNS = {
    "python": {
        "function": """
            (function_definition) @function
        """,
        "class": """
            (class_definition) @class
        """,
        "method": """
            (class_definition
                (block
                    (function_definition) @method))
        """,
        "import": """
            [(import_statement) (import_from_statement)] @import
        """,
        "call": """
            (call) @call
        """,
        "attribute": """
            (attribute) @attribute
        """,
        "string": """
            [(string) (string_content) (string_literal)] @string
        """,
        "comment": """
            (comment) @comment
        """,
        "error": """
            [(ERROR) (MISSING)] @error
        """,
        # Remove the separate missing pattern since it's combined with error
        # "missing": """
        #     (MISSING) @missing
        # """
    },
    # Add patterns for other languages as needed
}

# Default optimization settings by pattern type
DEFAULT_OPTIMIZATIONS = {
    "function": QueryOptimizationSettings(
        match_limit=100,
        max_start_depth=5
    ),
    "class": QueryOptimizationSettings(
        match_limit=50,
        max_start_depth=3
    ),
    "method": QueryOptimizationSettings(
        match_limit=200,
        max_start_depth=6
    ),
    "import": QueryOptimizationSettings(
        match_limit=50,
        max_start_depth=2
    ),
    "call": QueryOptimizationSettings(
        match_limit=500,
        max_start_depth=8
    ),
    "attribute": QueryOptimizationSettings(
        match_limit=300,
        max_start_depth=8
    ),
    "string": QueryOptimizationSettings(
        match_limit=1000,
        max_start_depth=10
    ),
    "comment": QueryOptimizationSettings(
        match_limit=1000,
        max_start_depth=10
    ),
    "error": QueryOptimizationSettings(
        match_limit=1000,  # High limit to catch all errors
        max_start_depth=20,  # Deep search for errors
        timeout_micros=None  # No timeout for error detection
    ),
    "missing": QueryOptimizationSettings(
        match_limit=1000,
        max_start_depth=20,
        timeout_micros=None
    )
}

def get_query_pattern(language: str, pattern_type: str) -> Optional[str]:
    """Get query pattern for language and type.
    
    Args:
        language: Language identifier
        pattern_type: Type of pattern to get
        
    Returns:
        Query pattern string or None if not found
    """
    if language not in QUERY_PATTERNS:
        return None
    return QUERY_PATTERNS[language].get(pattern_type)

def get_optimization_settings(pattern_type: str) -> QueryOptimizationSettings:
    """Get default optimization settings for a pattern type.
    
    Args:
        pattern_type: Type of pattern
        
    Returns:
        QueryOptimizationSettings with default values for the pattern
    """
    return DEFAULT_OPTIMIZATIONS.get(pattern_type, QueryOptimizationSettings()) 