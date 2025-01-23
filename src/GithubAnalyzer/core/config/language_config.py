"""Language configuration for tree-sitter."""
from typing import List, Optional
from tree_sitter_language_pack import installed_bindings_map, get_language, SupportedLanguage

# Common file extensions to language mappings
EXTENSION_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.cs': 'c_sharp',
    '.php': 'php',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.xml': 'xml',
    '.html': 'embedded_template'
}

def get_language_by_extension(extension: str) -> str:
    """Get language identifier from file extension.
    
    Args:
        extension: File extension including dot (e.g. '.py')
        
    Returns:
        Language identifier or 'unknown' if not found
    """
    # Add dot if not present
    if not extension.startswith('.'):
        extension = '.' + extension
    
    return EXTENSION_MAP.get(extension.lower(), 'unknown')

def get_supported_languages() -> List[str]:
    """Get list of supported languages.
    
    Returns:
        List of language identifiers that are supported by tree-sitter
    """
    supported = []
    for lang in ['python', 'javascript', 'typescript', 'c_sharp', 'php', 'yaml', 'xml', 'embedded_template']:
        try:
            get_language(lang)
            supported.append(lang)
        except LookupError:
            continue
    return supported

def get_file_types(language: str) -> List[str]:
    """Get list of file extensions for a language.
    
    Args:
        language: Language identifier
        
    Returns:
        List of file extensions including dot
    """
    extensions = []
    for ext, lang in EXTENSION_MAP.items():
        if lang == language:
            extensions.append(ext)
    return extensions
