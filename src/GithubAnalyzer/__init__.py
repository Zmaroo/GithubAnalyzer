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
from GithubAnalyzer.utils.logging.config import configure_logging

# Get logger for this module
logger = get_logger(__name__)

# Configure logging on package import
configure_logging()

# Import core components
try:
    from GithubAnalyzer.services.core.database.database_service import \
        DatabaseService
    from GithubAnalyzer.services.core.parser_service import ParserService
    CORE_SERVICES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Core services not available: {str(e)}")
    CORE_SERVICES_AVAILABLE = False

# Import models
from GithubAnalyzer.models.core.ast import NodeDict, NodeList
from GithubAnalyzer.models.core.base_model import BaseModel
from GithubAnalyzer.models.core.db.database import (Class, CodebaseQuery,
                                                    CodeSnippet,
                                                    DatabaseConfig,
                                                    DatabaseConnection,
                                                    DatabaseModel, File,
                                                    Function, GraphAnalytics)
from GithubAnalyzer.models.core.errors import (EditorError, LanguageError,
                                               ParserError, TraversalError,
                                               ValidationError)
from GithubAnalyzer.models.core.file import FileModel, FileInfo
from GithubAnalyzer.models.core.language import LanguageFeatures, LanguageInfo
from GithubAnalyzer.models.core.parsers import (CustomParseResult,
                                                EditorConfigResult,
                                                GitignoreResult,
                                                LockFileResult,
                                                RequirementsResult)
from GithubAnalyzer.models.core.repository import (ProcessingResult,
                                                   ProcessingStats,
                                                   RepositoryInfo)
from GithubAnalyzer.models.core.traversal import TreeSitterTraversal
from GithubAnalyzer.models.core.types import (FileId, FileType, LanguageId,
                                              LanguageType, NodeId, NodeType,
                                              QueryId, QueryType)

# Version
__version__ = "0.1.0"
__author__ = "Michael Marler"
__email__ = "michaelmarler@example.com"

# Services - Optional dependencies
try:
    from GithubAnalyzer.services.core.database.embedding_service import \
        CodeEmbeddingService as EmbeddingService
    EMBEDDING_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Embedding service not available: {str(e)}")
    EMBEDDING_SERVICE_AVAILABLE = False
    EmbeddingService = None

try:
    from GithubAnalyzer.services.core.database.neo4j_service import \
        Neo4jService
    NEO4J_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Neo4j service not available: {str(e)}")
    NEO4J_AVAILABLE = False
    Neo4jService = None

try:
    from GithubAnalyzer.services.core.database.postgres_service import \
        PostgresService
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

# Package exports
from .models import *
from .services import *
from .utils import *

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    # AST models
    'NodeDict', 'NodeList',
    'TreeSitterTraversal',
    
    # Base models
    'BaseModel',
    
    # Database models
    'DatabaseConfig', 'DatabaseConnection', 'DatabaseModel',
    'CodebaseQuery', 'CodeSnippet', 'File', 'Function', 'Class',
    'GraphAnalytics',
    
    # Error models
    'ParserError', 'EditorError', 'TraversalError',
    'ValidationError', 'LanguageError',
    
    # File models
    'FileModel', 'FileInfo',
    
    # Language models
    'LanguageFeatures', 'LanguageInfo',
    
    # Parser models
    'CustomParseResult', 'LockFileResult', 'RequirementsResult',
    'GitignoreResult', 'EditorConfigResult',
    
    # Repository models
    'RepositoryInfo', 'ProcessingStats', 'ProcessingResult',
    
    # Type definitions
    'FileId', 'LanguageId', 'NodeId', 'QueryId',
    'FileType', 'LanguageType', 'NodeType', 'QueryType',
    
    # Services
    'DatabaseService',
    'EmbeddingService',
    'Neo4jService',
    'PostgresService',
    'FileService',
    'ParserService',
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
