"""Configuration file patterns for repository analysis.

Note: Some config files (lock files, .env, .editorconfig) use custom parsers
instead of tree-sitter patterns. See GithubAnalyzer.services.parsers.core.custom_parsers
for those implementations.
"""

from .dockerfile_patterns import DOCKERFILE_PATTERNS
from .gitignore_patterns import GITIGNORE_PATTERNS
from .requirements_patterns import REQUIREMENTS_PATTERNS
from .makefile_patterns import MAKEFILE_PATTERNS

# Only include patterns for files with tree-sitter support
CONFIG_PATTERNS = {
    'dockerfile': DOCKERFILE_PATTERNS,
    'gitignore': GITIGNORE_PATTERNS,
    'requirements': REQUIREMENTS_PATTERNS,
    'makefile': MAKEFILE_PATTERNS
}

__all__ = [
    'CONFIG_PATTERNS',
    'DOCKERFILE_PATTERNS',
    'GITIGNORE_PATTERNS',
    'REQUIREMENTS_PATTERNS',
    'MAKEFILE_PATTERNS'
] 