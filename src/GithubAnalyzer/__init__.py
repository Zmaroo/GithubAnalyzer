"""
GitHub Code Analysis Tool
A tool for analyzing and processing GitHub repositories
"""

import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Version
__version__ = "0.1.0"

# Core layer imports
from .core.models import (
    ParseResult,
    ParserError,
    LanguageError,
    QueryError,
    FileOperationError,
    FileInfo
)

from .core.services import (
    FileService,
    ParserService
)

from .core.config.settings import Settings

# Analysis layer imports
from .analysis.models import (
    AnalysisResult,
    TreeSitterNode
)

from .analysis.services import (
    TreeSitterQueryHandler,
    TreeSitterTraversal
)

# Utils imports
from .core.utils import (
    Timer,
    StructuredLogger
)

__all__ = [
    # Core models
    'ParseResult',
    'ParserError',
    'LanguageError',
    'QueryError',
    'FileOperationError',
    'FileInfo',
    # Core services
    'FileService',
    'ParserService',
    # Core config
    'Settings',
    # Analysis models
    'AnalysisResult',
    'TreeSitterNode',
    # Analysis services
    'TreeSitterQueryHandler',
    'TreeSitterTraversal',
    # Utils exports
    'Timer',
    'StructuredLogger'
]

# Initialize settings
settings = Settings()
