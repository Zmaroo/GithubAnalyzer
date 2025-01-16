"""Language configuration."""

from typing import Dict, List, Optional, Union

# Supported tree-sitter languages from our dependencies
TREE_SITTER_LANGUAGES: Dict[str, Dict[str, Union[str, List[str]]]] = {
    "python": {
        "lib": "tree-sitter-python",
        "version": ">=0.23.6",
        "queries": ["functions", "classes"],
        "function_query": """
        (function_definition
          name: (identifier) @function.def)
        """
    },
    "javascript": {
        "lib": "tree-sitter-javascript",
        "version": ">=0.23.1",
        "queries": ["functions", "classes"],
        "function_query": """
        (function_declaration
          name: (identifier) @function.def)
        (method_definition
          name: (property_identifier) @function.def)
        (arrow_function
          name: (identifier) @function.def)
        """
    },
    "typescript": {
        "lib": "tree-sitter-typescript",
        "version": ">=0.23.2",
        "queries": ["functions", "classes"],
        "language_func": "language_typescript",
        "function_query": """
        (function_declaration
          name: (identifier) @function.def)
        (method_definition
          name: (property_identifier) @function.def)
        (arrow_function
          name: (identifier) @function.def)
        """
    },
    "tsx": {
        "lib": "tree-sitter-typescript",
        "version": ">=0.23.2",
        "queries": ["functions", "classes"],
        "language_func": "language_tsx",
        "function_query": """
        (function_declaration
          name: (identifier) @function.def)
        (method_definition
          name: (property_identifier) @function.def)
        """
    },
    "java": {
        "lib": "tree-sitter-java",
        "version": ">=0.23.5",
        "queries": ["functions", "classes"]
    },
    "cpp": {
        "lib": "tree-sitter-cpp",
        "version": ">=0.23.4",
        "queries": ["functions", "classes"]
    },
    "go": {
        "lib": "tree-sitter-go",
        "version": ">=0.23.4",
        "queries": ["functions"]
    }
}

# Map file types to parser languages
PARSER_LANGUAGE_MAP: Dict[str, str] = {
    # Core languages
    'python': 'python',
    'javascript': 'javascript',
    'typescript': 'typescript',
    'tsx': 'typescript',
    # System languages
    'c': 'c',
    'cpp': 'cpp',
    'cs': 'c-sharp',
    'java': 'java',
    'go': 'go',
    'rs': 'rust',
    # Scripting languages
    'rb': 'ruby',
    'php': 'php',
    'lua': 'lua',
    'groovy': 'groovy',
    'scala': 'scala',
    'kt': 'kotlin',
    # Web technologies
    'html': 'html',
    'css': 'css',
    'json': 'json',
    'yaml': 'yaml',
    'yml': 'yaml',
    'xml': 'xml',
    'md': 'markdown',
    'sql': 'sql',
    # Scientific/Engineering
    'matlab': 'matlab',
    'cuda': 'cuda',
    'ino': 'arduino',
    'toml': 'toml',
    # Common extensions
    'py': 'python',
    'js': 'javascript',
    'ts': 'typescript',
    'jsx': 'javascript',
}

def get_file_type_mapping() -> Dict[str, str]:
    """Get mapping of file extensions to language types."""
    return {f'.{ext}': lang for ext, lang in PARSER_LANGUAGE_MAP.items()}

def get_language_by_extension(extension: str) -> Optional[str]:
    """Get language type from file extension.
    
    Args:
        extension: File extension including dot (e.g., '.py')
        
    Returns:
        Language type or None if not supported
    """
    mapping = get_file_type_mapping()
    return mapping.get(extension.lower())

def get_language_variant(language: str) -> str:
    """Get language variant if applicable."""
    variants = {
        "typescript": "tsx",
        "javascript": "jsx",
        "cpp": "c_plus_plus",
        "c-sharp": "sharp"
    }
    return variants.get(language, language)
