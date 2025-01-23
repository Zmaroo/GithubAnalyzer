"""Tests for FileService."""
import pytest
from pathlib import Path

from src.GithubAnalyzer.core.models.errors import FileOperationError
from src.GithubAnalyzer.core.models.file import FileInfo, FileFilterConfig
from src.GithubAnalyzer.core.services.file_service import FileService

@pytest.fixture
def file_service():
    """Create a file service instance."""
    return FileService()

@pytest.fixture
def test_files(tmp_path):
    """Create test files."""
    files = {
        'test.py': 'python',
        'test.js': 'javascript',
        'test.cpp': 'cpp',
        'test.txt': 'unknown'
    }
    for name, lang in files.items():
        path = tmp_path / name
        path.write_text('test content')
    return tmp_path, files

def test_list_files(file_service, test_files):
    """Test listing files."""
    tmp_path, files = test_files
    file_list = file_service.list_files(tmp_path)
    assert len(file_list) == len(files)
    for file_info in file_list:
        assert isinstance(file_info, FileInfo)
        assert file_info.path.name in files
        assert file_info.language == files[file_info.path.name]

def test_filter_files(file_service, test_files):
    """Test filtering files."""
    tmp_path, files = test_files
    config = FileFilterConfig(
        include_languages=['python', 'javascript'],
        exclude_paths=['test.txt']
    )
    file_list = file_service.list_files(tmp_path, config)
    assert len(file_list) == 2
    languages = [f.language for f in file_list]
    assert 'python' in languages
    assert 'javascript' in languages 