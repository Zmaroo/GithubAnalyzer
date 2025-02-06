from typing import Any, Dict, Optional, Tuple, Union

"""Query patterns for tree-sitter.

Contains predefined patterns for common code elements and their optimization settings.
"""
from dataclasses import dataclass

from GithubAnalyzer.utils.logging import get_logger

from GithubAnalyzer.services.parsers.core.custom_parsers import get_custom_parser
from .language_patterns import (ADA_PATTERNS, BASH_PATTERNS, C_PATTERNS,
                                CLOJURE_PATTERNS, CPP_PATTERNS,
                                CSHARP_PATTERNS, DART_PATTERNS,
                                DOCKERFILE_PATTERNS, ELIXIR_PATTERNS,
                                GO_PATTERNS, GROOVY_PATTERNS, HASKELL_PATTERNS,
                                HTML_PATTERNS, JAVA_PATTERNS,
                                JS_VARIANT_PATTERNS,
                                KOTLIN_PATTERNS, LUA_PATTERNS,
                                MARKDOWN_PATTERNS, OBJECTIVEC_PATTERNS,
                                PERL_PATTERNS, PHP_PATTERNS,
                                POWERSHELL_PATTERNS, PYTHON_PATTERNS,
                                RACKET_PATTERNS, RUBY_PATTERNS, RUST_PATTERNS,
                                SCALA_PATTERNS, SQUIRREL_PATTERNS,
                                SWIFT_PATTERNS, TOML_PATTERNS, TS_PATTERNS,
                                YAML_PATTERNS)
from .templates import (COMMON_PATTERNS, COMMON_INTERFACE_PATTERNS,
                       COMMON_FUNCTION_DETAILS, COMMON_CLASS_DETAILS,
                       COMMON_CONTROL_FLOW, PATTERN_TEMPLATES)

# Common patterns shared across languages
COMMON_PATTERNS = {
    "function_definition": "(function_definition) @function",
    "class_definition": "(class_definition) @class",
    "method_definition": "(method_definition) @method",
    "variable_declaration": "(variable_declaration) @variable",
    "import_statement": "(import_statement) @import",
}

# Interface patterns for languages that support them
COMMON_INTERFACE_PATTERNS = {
    "interface_definition": "(interface_declaration) @interface",
    "interface_method": "(method_signature) @interface.method",
    "interface_property": "(property_signature) @interface.property",
}

# Function-related patterns
COMMON_FUNCTION_DETAILS = {
    "function_name": "(function_definition name: (identifier) @function.name)",
    "function_params": "(function_definition parameters: (parameter_list) @function.params)",
    "function_body": "(function_definition body: (block) @function.body)",
    "function_return": "(return_statement) @function.return",
}

# Class-related patterns
COMMON_CLASS_DETAILS = {
    "class_name": "(class_definition name: (identifier) @class.name)",
    "class_inheritance": "(class_definition superclass: (identifier) @class.parent)",
    "class_body": "(class_definition body: (class_body) @class.body)",
    "class_method": "(method_definition) @class.method",
    "class_property": "(property_definition) @class.property",
}

# Control flow patterns
COMMON_CONTROL_FLOW = {
    "if_statement": "(if_statement) @control.if",
    "else_clause": "(else_clause) @control.else",
    "for_loop": "(for_statement) @control.for",
    "while_loop": "(while_statement) @control.while",
    "try_block": "(try_statement) @control.try",
    "catch_clause": "(catch_clause) @control.catch",
    "finally_clause": "(finally_clause) @control.finally",
}

logger = get_logger(__name__)

# JavaScript/TypeScript variants
JS_VARIANTS = {"javascript", "jsx", "typescript", "tsx"}

# Mapping of file extensions to tree-sitter language names
EXTENSION_TO_LANGUAGE = {
    # Web Technologies
    'js': 'javascript',
    'jsx': 'javascript',
    'mjs': 'javascript',
    'cjs': 'javascript',
    'es': 'javascript',
    'es6': 'javascript',
    'iife.js': 'javascript',
    'bundle.js': 'javascript',
    'ts': 'typescript',
    'tsx': 'typescript',
    'mts': 'typescript',
    'cts': 'typescript',
    'html': 'html',
    'htm': 'html',
    'css': 'css',
    'scss': 'scss',
    'sass': 'scss',
    'less': 'css',
    'vue': 'vue',
    'svelte': 'svelte',
    
    # Systems Programming
    'c': 'c',
    'h': 'c',
    'cpp': 'cpp',
    'hpp': 'cpp',
    'cc': 'cpp',
    'cxx': 'cpp',
    'hxx': 'cpp',
    'h++': 'cpp',
    'cu': 'cuda',
    'cuh': 'cuda',
    'rs': 'rust',
    'go': 'go',
    'mod': 'gomod',
    'sum': 'gosum',
    'v': 'verilog',
    'sv': 'verilog',
    'vh': 'verilog',
    'vhd': 'vhdl',
    'vhdl': 'vhdl',
    
    # JVM Languages
    'java': 'java',
    'kt': 'kotlin',
    'kts': 'kotlin',
    'scala': 'scala',
    'sc': 'scala',
    'groovy': 'groovy',
    'gradle': 'groovy',
    
    # Scripting Languages
    'py': 'python',
    'pyi': 'python',
    'pyc': 'python',
    'pyd': 'python',
    'pyw': 'python',
    'rb': 'ruby',
    'rbw': 'ruby',
    'rake': 'ruby',
    'gemspec': 'ruby',
    'php': 'php',
    'php4': 'php',
    'php5': 'php',
    'php7': 'php',
    'php8': 'php',
    'phps': 'php',
    'lua': 'lua',
    'pl': 'perl',
    'pm': 'perl',
    't': 'perl',
    
    # Shell Scripting
    'sh': 'bash',
    'bash': 'bash',
    'zsh': 'bash',
    'fish': 'fish',
    'ksh': 'bash',
    'csh': 'bash',
    'tcsh': 'bash',
    
    # Functional Languages
    'hs': 'haskell',
    'lhs': 'haskell',
    'ml': 'ocaml',
    'mli': 'ocaml',
    'ex': 'elixir',
    'exs': 'elixir',
    'heex': 'heex',
    'clj': 'clojure',
    'cljs': 'clojure',
    'cljc': 'clojure',
    'edn': 'clojure',
    
    # Configuration & Data
    'yaml': 'yaml',
    'yml': 'yaml',
    'json': 'json',
    'jsonc': 'json',
    'toml': 'toml',
    'xml': 'xml',
    'xsl': 'xml',
    'xslt': 'xml',
    'svg': 'xml',
    'xaml': 'xml',
    'ini': 'ini',
    'cfg': 'ini',
    'conf': 'ini',
    
    # Build Systems
    'cmake': 'cmake',
    'make': 'make',
    'mk': 'make',
    'ninja': 'ninja',
    'bazel': 'starlark',
    'bzl': 'starlark',
    'BUILD': 'starlark',
    'WORKSPACE': 'starlark',
    
    # Documentation
    'md': 'markdown',
    'markdown': 'markdown',
    'rst': 'rst',
    'tex': 'latex',
    'latex': 'latex',
    'adoc': 'asciidoc',
    'asciidoc': 'asciidoc',
    
    # Other Languages
    'swift': 'swift',
    'dart': 'dart',
    'r': 'r',
    'rmd': 'r',
    'jl': 'julia',
    'zig': 'zig',
    
    # Query Languages
    'sql': 'sql',
    'mysql': 'sql',
    'pgsql': 'sql',
    'graphql': 'graphql',
    'gql': 'graphql',
    
    # Additional Languages
    'proto': 'protobuf',
    'thrift': 'thrift',
    'wasm': 'wasm',
    'wat': 'wat',
    'glsl': 'glsl',
    'hlsl': 'hlsl',
    'wgsl': 'wgsl',
    'dockerfile': 'dockerfile',
    'Dockerfile': 'dockerfile',
    'nginx.conf': 'nginx',
    'rules': 'udev',
    'hypr': 'hyprlang',
    'kdl': 'kdl',
    'ron': 'ron',
    'commonlisp': 'commonlisp',
    'elixir': 'elixir',
    # Add new mappings to EXTENSION_TO_LANGUAGE
    'rkt': 'racket',
    'lisp': 'commonlisp',
    'cl': 'commonlisp',
    'asd': 'commonlisp',
    'elm': 'elm',
    'erl': 'erlang',
    'hrl': 'erlang',
    'purs': 'purescript',
    'gleam': 'gleam',
    'hx': 'haxe',
    'hack': 'hack',
    'adb': 'ada',
    'ads': 'ada',
    'tcl': 'tcl',
    'nut': 'squirrel',
    'gd': 'gdscript',
    'sol': 'solidity',
    'ps1': 'powershell',
    'psm1': 'powershell',
    'psd1': 'powershell',
    'cs': 'c_sharp',
    'csx': 'c_sharp'
}

# Special filename mappings
SPECIAL_FILENAMES = {
    # Docker
    'dockerfile': 'dockerfile',
    'Dockerfile': 'dockerfile',
    'Dockerfile.dev': 'dockerfile',
    'Dockerfile.prod': 'dockerfile',
    
    # Build systems
    'makefile': 'make',
    'Makefile': 'make',
    'CMakeLists.txt': 'cmake',
    'meson.build': 'meson',
    'BUILD': 'starlark',
    'BUILD.bazel': 'starlark',
    'WORKSPACE': 'starlark',
    'WORKSPACE.bazel': 'starlark',
    'BUCK': 'starlark',
    
    # Git
    '.gitignore': 'gitignore',
    '.gitattributes': 'gitattributes',
    '.gitmodules': 'gitconfig',
    '.gitconfig': 'gitconfig',
    
    # Shell
    '.bashrc': 'bash',
    '.zshrc': 'bash',
    '.bash_profile': 'bash',
    '.profile': 'bash',
    '.zprofile': 'bash',
    
    # Python
    'requirements.txt': 'requirements',
    'constraints.txt': 'requirements',
    'Pipfile': 'toml',
    'pyproject.toml': 'toml',
    'poetry.lock': 'toml',
    'setup.py': 'python',
    'setup.cfg': 'ini',
    'tox.ini': 'ini',
    
    # JavaScript/Node
    'package.json': 'json',
    'package-lock.json': 'json',
    'yarn.lock': 'yaml',
    'pnpm-lock.yaml': 'yaml',
    'webpack.config.js': 'javascript',
    'rollup.config.js': 'javascript',
    'babel.config.js': 'javascript',
    '.babelrc': 'json',
    '.babelrc.json': 'json',
    'tsconfig.json': 'json',
    
    # Rust
    'Cargo.toml': 'toml',
    'Cargo.lock': 'toml',
    
    # Editor/IDE
    '.editorconfig': 'properties',
    '.vscode/settings.json': 'json',
    '.idea/workspace.xml': 'xml',
    
    # Environment/Config
    '.env': 'properties',
    '.env.local': 'properties',
    '.env.development': 'properties',
    '.env.production': 'properties',
    
    # Other
    'XCompose': 'xcompose',
    '.luacheckrc': 'lua',
    '.styluarc': 'lua',
    'CHANGELOG.md': 'markdown',
    'README.md': 'markdown',
    'LICENSE': 'text',
    'Procfile': 'properties',
    'docker-compose.yml': 'yaml',
    'docker-compose.yaml': 'yaml'
}

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
    "python": PYTHON_PATTERNS,
    **JS_VARIANT_PATTERNS,  # Add JavaScript variants
    "c": C_PATTERNS,
    "yaml": YAML_PATTERNS,
    "toml": TOML_PATTERNS,
    "dockerfile": DOCKERFILE_PATTERNS,
    "markdown": MARKDOWN_PATTERNS,
    "java": JAVA_PATTERNS,
    "go": GO_PATTERNS,
    "rust": RUST_PATTERNS,
    "cpp": CPP_PATTERNS,
    "ruby": RUBY_PATTERNS,
    "php": PHP_PATTERNS,
    "swift": SWIFT_PATTERNS,
    "kotlin": KOTLIN_PATTERNS,
    "html": HTML_PATTERNS,
    "bash": BASH_PATTERNS,
    "dart": DART_PATTERNS,
    "elixir": ELIXIR_PATTERNS,
    "ada": ADA_PATTERNS,
    "haskell": HASKELL_PATTERNS,
    "perl": PERL_PATTERNS,
    "objective-c": OBJECTIVEC_PATTERNS,
    "lua": LUA_PATTERNS,
    "scala": SCALA_PATTERNS,
    "groovy": GROOVY_PATTERNS,
    "racket": RACKET_PATTERNS,
    "clojure": CLOJURE_PATTERNS,
    "squirrel": SQUIRREL_PATTERNS,
    "powershell": POWERSHELL_PATTERNS,
    "csharp": CSHARP_PATTERNS,
    "typescript": TS_PATTERNS,
    # Additional languages can be added here
}

# Common patterns that apply to most languages
COMMON_PATTERNS = {
    "comment": """
        [
          (comment) @comment.line
          (block_comment) @comment.block
        ] @comment
    """,
    "string": """
        [
          (string_literal) @string
          (raw_string_literal) @string.raw
        ] @string.any
    """,
    "error": """
        [
          (ERROR) @error.syntax
          (MISSING) @error.missing
          (_
            (#is? @error.incomplete incomplete)
            (#is-not? @error.incomplete complete)) @error
        ]
    """
}

# Add common patterns to all languages
def get_language_patterns(language: str) -> Dict[str, str]:
    """Get all patterns for a language, including common patterns.
    
    Args:
        language: Language identifier
        
    Returns:
        Dictionary of pattern type to pattern string
    """
    # Get base patterns for language
    patterns = QUERY_PATTERNS.get(language, {}).copy()
    
    # Add common patterns only if not already defined
    for pattern_type, pattern in COMMON_PATTERNS.items():
        if pattern_type not in patterns:
            patterns[pattern_type] = pattern
            
    return patterns

# Default optimization settings by pattern type
DEFAULT_OPTIMIZATIONS = {
    "function": QueryOptimizationSettings(
        match_limit=100,
        max_start_depth=5,
        timeout_micros=1000
    ),
    "class": QueryOptimizationSettings(
        match_limit=50,
        max_start_depth=3,
        timeout_micros=1000
    ),
    "method": QueryOptimizationSettings(
        match_limit=200,
        max_start_depth=6,
        timeout_micros=1000
    ),
    "import": QueryOptimizationSettings(
        match_limit=50,
        max_start_depth=2,
        timeout_micros=500
    ),
    "interface": QueryOptimizationSettings(
        match_limit=50,
        max_start_depth=3,
        timeout_micros=1000
    ),
    "struct": QueryOptimizationSettings(
        match_limit=50,
        max_start_depth=3,
        timeout_micros=1000
    ),
    "namespace": QueryOptimizationSettings(
        match_limit=30,
        max_start_depth=2,
        timeout_micros=500
    ),
    "comment": QueryOptimizationSettings(
        match_limit=1000,
        max_start_depth=10,
        timeout_micros=1000
    ),
    "string": QueryOptimizationSettings(
        match_limit=1000,
        max_start_depth=10,
        timeout_micros=1000
    ),
    "error": QueryOptimizationSettings(
        match_limit=1000,
        max_start_depth=20,
        timeout_micros=5000
    )
}

# Helper function to get language for a file
def get_language_for_file(filename: str) -> Optional[str]:
    """Get the language for a file based on its name or extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        Language identifier or None if not found
    """
    logger.debug("Detecting language for file", extra={
        'context': {
            'operation': 'language_detection',
            'file': filename
        }
    })
    
    # First check if there's a custom parser
    if get_custom_parser(filename):
        logger.debug("Found custom parser", extra={
            'context': {
                'operation': 'language_detection',
                'file': filename,
                'detection_method': 'custom_parser'
            }
        })
        # Let the FileService._detect_language handle custom parser language mapping
        return None
        
    # Then check special filenames
    if filename in SPECIAL_FILENAMES:
        language = SPECIAL_FILENAMES[filename]
        logger.debug("Language detected from special filename", extra={
            'context': {
                'operation': 'language_detection',
                'file': filename,
                'language': language,
                'detection_method': 'special_filename'
            }
        })
        return language
        
    # Finally check extensions
    ext = filename.split('.')[-1].lower() if '.' in filename else filename.lower()
    language = EXTENSION_TO_LANGUAGE.get(ext)
    
    if language:
        logger.debug("Language detected from extension", extra={
            'context': {
                'operation': 'language_detection',
                'file': filename,
                'extension': ext,
                'language': language,
                'detection_method': 'extension'
            }
        })
    else:
        logger.debug("No language detected", extra={
            'context': {
                'operation': 'language_detection',
                'file': filename,
                'extension': ext,
                'detection_method': 'extension'
            }
        })
        
    return language

# Update get_query_pattern to use get_language_patterns
def get_query_pattern(language: str, pattern_type: str) -> Optional[str]:
    """Get query pattern for language and type.
    
    Args:
        language: Language identifier
        pattern_type: Type of pattern to get
        
    Returns:
        Query pattern string or None if not found
    """
    logger.debug("Getting query pattern", extra={
        'context': {
            'operation': 'get_pattern',
            'language': language,
            'pattern_type': pattern_type
        }
    })
    
    # Skip pattern lookup for custom parser languages
    if language in {'requirements', 'env', 'gitignore', 'editorconfig', 'lockfile'}:
        logger.debug("Skipping pattern lookup for custom parser language", extra={
            'context': {
                'operation': 'get_pattern',
                'language': language,
                'pattern_type': pattern_type
            }
        })
        return None
        
    # First try to get the actual language if this is a filename
    if '.' in language or language in SPECIAL_FILENAMES:
        detected_lang = get_language_for_file(language)
        if detected_lang:
            language = detected_lang
        
    # Get all patterns for the language
    patterns = get_language_patterns(language)
    if pattern_type in patterns:
        logger.debug("Found pattern", extra={
            'context': {
                'operation': 'get_pattern',
                'language': language,
                'pattern_type': pattern_type,
                'pattern_found': True
            }
        })
        return patterns[pattern_type]
        
    # Try base language if not found
    base_lang = get_base_language(language)
    if base_lang != language:
        patterns = get_language_patterns(base_lang)
        if pattern_type in patterns:
            logger.debug("Found pattern in base language", extra={
                'context': {
                    'operation': 'get_pattern',
                    'language': language,
                    'base_language': base_lang,
                    'pattern_type': pattern_type,
                    'pattern_found': True
                }
            })
            return patterns[pattern_type]
            
    logger.debug("Pattern not found", extra={
        'context': {
            'operation': 'get_pattern',
            'language': language,
            'pattern_type': pattern_type,
            'pattern_found': False
        }
    })
    return None

# Update get_optimization_settings to handle variants
def get_optimization_settings(pattern_type: str, language: Optional[str] = None) -> QueryOptimizationSettings:
    """Get default optimization settings for a pattern type.
    
    Args:
        pattern_type: Type of pattern
        language: Optional language identifier
        
    Returns:
        QueryOptimizationSettings with default values for the pattern
    """
    logger.debug("Getting optimization settings", extra={
        'context': {
            'operation': 'get_settings',
            'pattern_type': pattern_type,
            'language': language
        }
    })
    
    # Get base settings
    settings = DEFAULT_OPTIMIZATIONS.get(pattern_type, QueryOptimizationSettings())
    
    # Apply language-specific adjustments
    if language and is_js_variant(language):
        # Increase limits for JSX/TSX
        if language.lower() in {'jsx', 'tsx'} and pattern_type in {'function', 'class', 'jsx_element'}:
            settings.match_limit *= 2  # Double the limits for JSX/TSX
            settings.max_start_depth += 5  # Increase depth for nested elements
            
            logger.debug("Applied JSX/TSX optimizations", extra={
                'context': {
                    'operation': 'get_settings',
                    'pattern_type': pattern_type,
                    'language': language,
                    'match_limit': settings.match_limit,
                    'max_start_depth': settings.max_start_depth
                }
            })
            
    return settings 

def is_js_variant(language: str) -> bool:
    """Check if a language is a JavaScript variant.
    
    Args:
        language: Language identifier
        
    Returns:
        True if language is a JavaScript variant
    """
    return language.lower() in JS_VARIANTS

def get_base_language(language: Optional[str]) -> str:
    """Get base language for variants.
    
    Args:
        language: Language identifier
        
    Returns:
        Base language (e.g., 'javascript' for 'jsx')
    """
    if not language:
        return "python"  # Default to Python as our primary language
        
    language = language.lower()
    if language in {'jsx', 'tsx', 'javascript', 'typescript'}:
        return 'javascript'  # All JS variants use the same base patterns
    elif language in {'hpp', 'cc', 'hh'}:
        return 'cpp'
    return language 