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
    FileInfo,
    FileFilterConfig,
    ParseResult,
    ParserError,
    LanguageError,
    QueryError,
    FileOperationError
)

from .core.services import (
    FileService,
    ParserService
)

from .core.config import (
    settings,
    Settings,
    get_logging_config
)

# Analysis layer imports
from .analysis.models import (
    get_node_text,
    node_to_dict,
    format_error_context,
    count_nodes,
    CodeAnalysisResult,
    AnalysisResult
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
    'FileInfo',
    'FileFilterConfig',
    'ParseResult',
    'ParserError',
    'LanguageError',
    'QueryError',
    'FileOperationError',
    # Core services
    'FileService',
    'ParserService',
    # Core config
    'settings',
    'Settings',
    'get_logging_config',
    # Analysis models
    'get_node_text',
    'node_to_dict',
    'format_error_context',
    'count_nodes',
    'CodeAnalysisResult',
    'AnalysisResult',
    # Analysis services
    'TreeSitterQueryHandler',
    'TreeSitterTraversal',
    # Utils exports
    'Timer',
    'StructuredLogger'
]

# Initialize settings
settings = Settings()
