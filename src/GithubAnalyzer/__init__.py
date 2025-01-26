"""
GithubAnalyzer package.

This package provides tools for analyzing GitHub repositories.
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

# Models
from GithubAnalyzer.models.core.database import (
    CodeSnippet,
    Function,
    File,
    CodebaseQuery,
)

# Services
from GithubAnalyzer.services.core.database.database_service import DatabaseService
from GithubAnalyzer.services.core.database.embedding_service import CodeEmbeddingService as EmbeddingService
from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
from GithubAnalyzer.services.core.database.postgres_service import PostgresService
from GithubAnalyzer.services.core.file_service import FileService
from GithubAnalyzer.services.core.parser_service import ParserService

# Utils
from GithubAnalyzer.utils.timing import Timer, timer
from GithubAnalyzer.utils.logging.logging_config import get_logger

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
    
    # Utils
    'Timer',
    'timer',
    'get_logger',
]
