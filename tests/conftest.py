"""Test configuration and fixtures."""
import os
import sys
from pathlib import Path
import pytest

# Get the absolute path of the project root
project_root = Path(__file__).parent.parent

# Add the project root to Python path
sys.path.insert(0, str(project_root))

# Common fixtures
@pytest.fixture(scope="session")
def cache_service():
    """Create a CacheService instance."""
    from src.GithubAnalyzer.common.services.cache_service import CacheService
    service = CacheService()
    service.initialize()
    yield service
    service.cleanup()

@pytest.fixture(scope="session")
def file_service():
    """Create a FileService instance."""
    from src.GithubAnalyzer.core.services.file_service import FileService
    service = FileService()
    service.initialize()
    yield service
    service.cleanup() 