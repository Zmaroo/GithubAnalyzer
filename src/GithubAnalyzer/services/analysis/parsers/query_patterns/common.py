"""Common query patterns and optimization settings for tree-sitter parsers.

This module exports:
    - COMMON_PATTERNS: A dictionary of common query patterns (for comments, strings, and errors).
    - DEFAULT_OPTIMIZATIONS: A dictionary of default optimization settings for various pattern types.
    - get_language_patterns: A helper function that merges language-specific patterns with common patterns.
"""

COMMON_PATTERNS = {
    "comment": """\
        [
          (comment) @comment.line
          (block_comment) @comment.block
        ] @comment
    """,
    "string": """\
        [
          (string_literal) @string
          (raw_string_literal) @string.raw
        ] @string.any
    """,
    "error": """\
        [
          (ERROR) @error.syntax
          (MISSING) @error.missing
          ( _ (#is? @error.incomplete incomplete) (#is-not? @error.incomplete complete) ) @error
        ]
    """
}

DEFAULT_OPTIMIZATIONS = {
    "function": {
        "match_limit": 100,
        "max_start_depth": 5,
        "timeout_micros": 1000
    },
    "class": {
        "match_limit": 50,
        "max_start_depth": 3,
        "timeout_micros": 1000
    },
    "method": {
        "match_limit": 200,
        "max_start_depth": 6,
        "timeout_micros": 1000
    },
    "import": {
        "match_limit": 50,
        "max_start_depth": 2,
        "timeout_micros": 500
    },
    "interface": {
        "match_limit": 50,
        "max_start_depth": 3,
        "timeout_micros": 1000
    },
    "struct": {
        "match_limit": 50,
        "max_start_depth": 3,
        "timeout_micros": 1000
    },
    "namespace": {
        "match_limit": 30,
        "max_start_depth": 2,
        "timeout_micros": 500
    },
    "comment": {
        "match_limit": 1000,
        "max_start_depth": 10,
        "timeout_micros": 1000
    },
    "string": {
        "match_limit": 1000,
        "max_start_depth": 10,
        "timeout_micros": 1000
    },
    "error": {
        "match_limit": 1000,
        "max_start_depth": 20,
        "timeout_micros": 5000
    }
}

def get_language_patterns(language: str, base_patterns: dict) -> dict:
    """Merge base_patterns with common patterns for a language.
    
    Args:
        language: Language identifier (unused here but kept for interface consistency).
        base_patterns: A dictionary of language-specific patterns.
    
    Returns:
        A merged dictionary with common patterns injected if missing.
    """
    patterns = base_patterns.copy()
    for pattern_type, pattern in COMMON_PATTERNS.items():
        if pattern_type not in patterns:
            patterns[pattern_type] = pattern
    return patterns 