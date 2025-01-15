"""Language configuration."""

from typing import Dict, List, Optional

# Supported tree-sitter languages from our dependencies
TREE_SITTER_LANGUAGES = [
    "python",
    "javascript",
    "typescript",
    "java",
    "cpp",
    "go",
    "ruby",
    "php",
    "c",
    "c-sharp",
    "scala",
    "kotlin",
    "lua",
    "bash",
    "html",
    "css",
    "json",
    "yaml",
    "toml",
    "xml",
    "markdown",
    "sql",
    "arduino",
    "cuda",
    "groovy",
    "matlab"
]

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
