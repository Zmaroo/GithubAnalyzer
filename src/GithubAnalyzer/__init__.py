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

# Import core components first
from .core.models import ast, errors, file
from .core.services.base_service import BaseService
from .core.services.file_service import FileService
from .core.services.parser_service import ParserService

# Then analysis components
from .analysis.models.tree_sitter import TreeSitterError, TreeSitterResult
from .analysis.services.parsers.tree_sitter import TreeSitterParser

# Finally common components
from .common.services.cache_service import CacheService

# Core layer exports
from .core.models.ast import ParseResult
from .core.models.errors import ServiceError, ParserError, FileOperationError
from .core.models.file import FileInfo, FileType
from .core.config.settings import Settings

# Analysis layer exports
from .analysis.models.results import AnalysisResult

__all__ = [
    # Core models
    "ParseResult",
    "ServiceError",
    "ParserError", 
    "FileOperationError",
    "FileInfo",
    "FileType",
    # Core config
    "Settings",
    # Analysis models
    "AnalysisResult",
    # Analysis services
    "TreeSitterParser",
]

# Initialize settings
settings = Settings()
