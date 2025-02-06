"""Core language models and definitions."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from tree_sitter import Language, Parser

from GithubAnalyzer.models.core.base_model import BaseModel
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class LanguageFeatures:
    """Features supported by a programming language."""
    has_types: bool = False
    has_classes: bool = False
    has_functions: bool = True
    has_modules: bool = False
    has_decorators: bool = False
    has_docstrings: bool = False
    has_interfaces: bool = False
    has_generics: bool = False
    has_async: bool = False
    has_exceptions: bool = True
    
    def __post_init__(self):
        """Initialize language features."""
        logger.debug("Language features initialized", extra={
            'context': {
                'features': {
                    'types': self.has_types,
                    'classes': self.has_classes,
                    'functions': self.has_functions,
                    'modules': self.has_modules,
                    'decorators': self.has_decorators,
                    'docstrings': self.has_docstrings,
                    'interfaces': self.has_interfaces,
                    'generics': self.has_generics,
                    'async': self.has_async,
                    'exceptions': self.has_exceptions
                }
            }
        })

@dataclass
class LanguageInfo(BaseModel):
    """Information about a programming language."""
    name: str
    extensions: List[str] = field(default_factory=list)
    filenames: List[str] = field(default_factory=list)
    features: LanguageFeatures = field(default_factory=LanguageFeatures)
    parser: Optional[Parser] = None
    language_object: Optional[Language] = None
    is_supported: bool = True
    
    def __post_init__(self):
        """Initialize language info."""
        super().__post_init__()
        self._log("debug", "Language info initialized",
                name=self.name,
                extension_count=len(self.extensions),
                filename_count=len(self.filenames),
                has_parser=self.parser is not None,
                has_language_object=self.language_object is not None,
                is_supported=self.is_supported)

# Core language mappings
EXTENSION_TO_LANGUAGE = {
    # Web
    'js': 'javascript',
    'jsx': 'javascript',
    'ts': 'typescript',
    'tsx': 'typescript',
    'html': 'html',
    'css': 'css',
    
    # Python
    'py': 'python',
    'pyi': 'python',
    
    # System
    'c': 'c',
    'h': 'c',
    'cpp': 'cpp',
    'hpp': 'cpp',
    'rs': 'rust',
    'go': 'go',
    
    # JVM
    'java': 'java',
    'kt': 'kotlin',
    'scala': 'scala',
    
    # Other
    'rb': 'ruby',
    'php': 'php',
    'sh': 'bash',
    'yaml': 'yaml',
    'yml': 'yaml',
    'json': 'json',
    'md': 'markdown'
}

SPECIAL_FILENAMES = {
    'dockerfile': 'dockerfile',
    'makefile': 'makefile',
    'jenkinsfile': 'groovy',
    'rakefile': 'ruby',
    'gemfile': 'ruby'
}

# Language support sets
INTERFACE_LANGUAGES = {'typescript', 'java', 'c_sharp'}
CLASS_LANGUAGES = {'typescript', 'java', 'c_sharp', 'python'}
JS_VARIANTS = {'javascript', 'jsx', 'typescript', 'tsx'}
STATICALLY_TYPED_LANGUAGES = {'typescript', 'java', 'c_sharp', 'c', 'cpp', 'rust', 'go'}

# Core language feature definitions
LANGUAGE_FEATURES = {
    'python': LanguageFeatures(
        has_types=True,
        has_classes=True,
        has_functions=True,
        has_modules=True,
        has_decorators=True,
        has_docstrings=True,
        has_async=True,
        has_exceptions=True
    ),
    'javascript': LanguageFeatures(
        has_classes=True,
        has_functions=True,
        has_modules=True,
        has_async=True,
        has_exceptions=True
    ),
    'typescript': LanguageFeatures(
        has_types=True,
        has_classes=True,
        has_functions=True,
        has_modules=True,
        has_interfaces=True,
        has_generics=True,
        has_async=True,
        has_exceptions=True
    )
}

def is_js_variant(language: str) -> bool:
    """Check if a language is a JavaScript variant."""
    return language.lower() in JS_VARIANTS

def get_base_language(language: Optional[str]) -> str:
    """Get base language for variants."""
    if not language:
        return "python"  # Default to Python as our primary language
        
    language = language.lower()
    if language in JS_VARIANTS:
        return 'javascript'  # All JS variants use the same base patterns
    elif language in {'hpp', 'cc', 'hh'}:
        return 'cpp'
    return language

def supports_interfaces(language: str) -> bool:
    """Check if a language supports interfaces."""
    return language.lower() in INTERFACE_LANGUAGES

def supports_classes(language: str) -> bool:
    """Check if a language supports classes."""
    return language.lower() in CLASS_LANGUAGES

def is_statically_typed(language: str) -> bool:
    """Check if a language is statically typed."""
    return language.lower() in STATICALLY_TYPED_LANGUAGES 