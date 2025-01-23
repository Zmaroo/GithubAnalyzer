"""Tree-sitter query patterns."""
from typing import Dict, Optional

# Query patterns by language
QUERY_PATTERNS = {
    "python": {
        "function": """
            (function_definition
                name: (identifier) @function.name
            ) @function.definition
        """,
        "class": """
            (class_definition
                name: (identifier) @class.name
            ) @class.definition
        """,
        "import": """
            (import_statement) @import
            (import_from_statement) @import
        """
    },
    # Add patterns for other languages...
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