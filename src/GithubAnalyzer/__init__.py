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
from GithubAnalyzer.utils.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)

# Import core components
try:
    from GithubAnalyzer.services.core.database.database_service import DatabaseService
    from GithubAnalyzer.services.core.parser_service import ParserService
    CORE_SERVICES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Core services not available: {str(e)}")
    CORE_SERVICES_AVAILABLE = False

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

# Services - Optional dependencies
try:
    from GithubAnalyzer.services.core.database.embedding_service import CodeEmbeddingService as EmbeddingService
    EMBEDDING_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Embedding service not available: {str(e)}")
    EMBEDDING_SERVICE_AVAILABLE = False
    EmbeddingService = None

try:
    from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
    NEO4J_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Neo4j service not available: {str(e)}")
    NEO4J_AVAILABLE = False
    Neo4jService = None

try:
    from GithubAnalyzer.services.core.database.postgres_service import PostgresService
    POSTGRES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"PostgreSQL service not available: {str(e)}")
    POSTGRES_AVAILABLE = False
    PostgresService = None

try:
    from GithubAnalyzer.services.core.file_service import FileService
    FILE_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"File service not available: {str(e)}")
    FILE_SERVICE_AVAILABLE = False
    FileService = None

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
    
    # Availability flags
    'CORE_SERVICES_AVAILABLE',
    'EMBEDDING_SERVICE_AVAILABLE',
    'NEO4J_AVAILABLE',
    'POSTGRES_AVAILABLE',
    'FILE_SERVICE_AVAILABLE'
]
