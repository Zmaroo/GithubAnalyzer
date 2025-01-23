"""Test fixtures and configuration."""
import os
import sys
import pytest
import logging
from pathlib import Path
from typing import Generator, List

from tree_sitter_language_pack import get_language

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.GithubAnalyzer.core.services.file_service import FileService
from src.GithubAnalyzer.core.services.parser_service import ParserService
from src.GithubAnalyzer.core.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

def get_supported_languages() -> List[str]:
    """Get all languages supported by tree-sitter-language-pack."""
    languages = []
    for lang in ['python', 'javascript', 'typescript', 'cpp', 'c', 'java', 'ruby', 'go', 'rust', 'php', 'c_sharp']:
        try:
            get_language(lang)
            languages.append(lang)
        except LookupError:
            logger.warning(f"Language {lang} is not supported")
    return languages

@pytest.fixture(scope="session")
def languages() -> List[str]:
    """Get supported languages from tree-sitter-language-pack."""
    return get_supported_languages()

@pytest.fixture
def file_service() -> FileService:
    """Get file service instance."""
    return FileService()

@pytest.fixture
def parser_service() -> ParserService:
    """Get parser service instance."""
    return ParserService()

@pytest.fixture
def test_files(tmp_path: Path) -> Generator[Path, None, None]:
    """Create test files with different languages."""
    files = {
        'test.py': ('python', 'def test(): pass'),
        'test.js': ('javascript', 'function test() {}'),
        'test.cpp': ('cpp', 'void test() {}'),
        'test.unknown': ('unknown', 'test content')
    }
    
    for name, (_, content) in files.items():
        path = tmp_path / name
        path.write_text(content)
        
    yield tmp_path 