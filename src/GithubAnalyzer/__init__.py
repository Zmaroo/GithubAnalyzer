"""
GithubAnalyzer package.

This package provides tools for analyzing GitHub repositories.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = str(Path(__file__).parent.parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Set up logging
from GithubAnalyzer.utils.logging import get_logger, configure_logging

# Configure logging
configure_logging()

# Get logger for this module
logger = get_logger(__name__)

# Import core components
from GithubAnalyzer.services.core.database.database_service import DatabaseService
from GithubAnalyzer.services.core.parser_service import ParserService

# Import models
from GithubAnalyzer.models.core.errors import (
    ParserError,
    ServiceError,
    FileOperationError,
    ConfigError
)

# Version
__version__ = "0.1.0"

# Models
from GithubAnalyzer.models.core.database import (
    CodeSnippet,
    Function,
    File,
    CodebaseQuery,
)

# Services
from GithubAnalyzer.services.core.database.embedding_service import CodeEmbeddingService as EmbeddingService
from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
from GithubAnalyzer.services.core.database.postgres_service import PostgresService
from GithubAnalyzer.services.core.file_service import FileService

# Utils
from GithubAnalyzer.utils.timing import Timer, timer

__all__ = [
    # Models
    'CodeSnippet',
    'Function',
    'File',
    'CodebaseQuery',
    
    # Services
    'DatabaseService',
    'EmbeddingService',
    'Neo4jService',
    'PostgresService',
    'FileService',
    'ParserService',
    'ParserError',
    'ServiceError',
    'FileOperationError',
    'ConfigError',
]
