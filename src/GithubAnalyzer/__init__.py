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

# Core layer exports
from .core.models.ast import ParseResult
from .core.models.errors import ServiceError, ParserError, FileOperationError
from .core.models.file import FileInfo, FileType
from .core.config.settings import Settings

# Analysis layer exports
from .analysis.models.results import AnalysisResult
from .analysis.services.parsers.tree_sitter import TreeSitterParser

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
