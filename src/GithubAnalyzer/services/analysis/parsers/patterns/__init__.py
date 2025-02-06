"""Tree-sitter query patterns package.

This package contains all the tree-sitter query patterns used for code analysis,
organized by language and pattern type.
"""
from typing import Dict, Any

# Import language-specific patterns
from .languages.common import JS_TS_SHARED_PATTERNS
from .languages.typescript import TS_PATTERNS
from .languages.python import PYTHON_PATTERNS
from .languages.java import JAVA_PATTERNS
from .languages.cpp import CPP_PATTERNS
from .languages.csharp import CSHARP_PATTERNS
from .languages.go import GO_PATTERNS
from .languages.rust import RUST_PATTERNS
from .languages.ruby import RUBY_PATTERNS
from .languages.php import PHP_PATTERNS
from .languages.swift import SWIFT_PATTERNS
from .languages.kotlin import KOTLIN_PATTERNS
from .languages.scala import SCALA_PATTERNS
from .languages.sql import SQL_PATTERNS

# Import markup patterns
from .languages.markup import (
    HTML_PATTERNS,
    YAML_PATTERNS,
    TOML_PATTERNS,
    DOCKERFILE_PATTERNS,
    MARKDOWN_PATTERNS,
    REQUIREMENTS_PATTERNS,
    GITIGNORE_PATTERNS,
    MAKEFILE_PATTERNS
)

# Import other language patterns
from .languages.ada import ADA_PATTERNS
from .languages.haskell import HASKELL_PATTERNS
from .languages.perl import PERL_PATTERNS
from .languages.objectivec import OBJECTIVEC_PATTERNS
from .languages.lua import LUA_PATTERNS
from .languages.groovy import GROOVY_PATTERNS
from .languages.racket import RACKET_PATTERNS
from .languages.clojure import CLOJURE_PATTERNS
from .languages.squirrel import SQUIRREL_PATTERNS
from .languages.powershell import POWERSHELL_PATTERNS

# Language pattern registry
LANGUAGE_PATTERNS: Dict[str, Dict[str, Any]] = {
    'python': PYTHON_PATTERNS,
    'javascript': JS_TS_SHARED_PATTERNS,  # Using shared patterns for JavaScript
    'typescript': TS_PATTERNS,
    'java': JAVA_PATTERNS,
    'cpp': CPP_PATTERNS,
    'csharp': CSHARP_PATTERNS,
    'go': GO_PATTERNS,
    'rust': RUST_PATTERNS,
    'ruby': RUBY_PATTERNS,
    'php': PHP_PATTERNS,
    'swift': SWIFT_PATTERNS,
    'kotlin': KOTLIN_PATTERNS,
    'scala': SCALA_PATTERNS,
    'sql': SQL_PATTERNS,
    'html': HTML_PATTERNS,
    'yaml': YAML_PATTERNS,
    'toml': TOML_PATTERNS,
    'dockerfile': DOCKERFILE_PATTERNS,
    'markdown': MARKDOWN_PATTERNS,
    'requirements': REQUIREMENTS_PATTERNS,
    'gitignore': GITIGNORE_PATTERNS,
    'make': MAKEFILE_PATTERNS,
    'ada': ADA_PATTERNS,
    'haskell': HASKELL_PATTERNS,
    'perl': PERL_PATTERNS,
    'objectivec': OBJECTIVEC_PATTERNS,
    'lua': LUA_PATTERNS,
    'groovy': GROOVY_PATTERNS,
    'racket': RACKET_PATTERNS,
    'clojure': CLOJURE_PATTERNS,
    'squirrel': SQUIRREL_PATTERNS,
    'powershell': POWERSHELL_PATTERNS
}

# Shared patterns for JavaScript/TypeScript
JS_TS_PATTERNS = JS_TS_SHARED_PATTERNS

__all__ = [
    'LANGUAGE_PATTERNS',
    'JS_TS_PATTERNS',
    # Individual language patterns
    'PYTHON_PATTERNS',
    'TS_PATTERNS',
    'JAVA_PATTERNS',
    'CPP_PATTERNS',
    'CSHARP_PATTERNS',
    'GO_PATTERNS',
    'RUST_PATTERNS',
    'RUBY_PATTERNS',
    'PHP_PATTERNS',
    'SWIFT_PATTERNS',
    'KOTLIN_PATTERNS',
    'SCALA_PATTERNS',
    'SQL_PATTERNS',
    # Markup patterns
    'HTML_PATTERNS',
    'YAML_PATTERNS',
    'TOML_PATTERNS',
    'DOCKERFILE_PATTERNS',
    'MARKDOWN_PATTERNS',
    'REQUIREMENTS_PATTERNS',
    'GITIGNORE_PATTERNS',
    'MAKEFILE_PATTERNS',
    # Other language patterns
    'ADA_PATTERNS',
    'HASKELL_PATTERNS',
    'PERL_PATTERNS',
    'OBJECTIVEC_PATTERNS',
    'LUA_PATTERNS',
    'GROOVY_PATTERNS',
    'RACKET_PATTERNS',
    'CLOJURE_PATTERNS',
    'SQUIRREL_PATTERNS',
    'POWERSHELL_PATTERNS'
] 