"""Tests for the file service.

This module contains tests for verifying proper functionality
of the file service component.
"""

import os
from pathlib import Path
import pytest
from typing import Generator

from GithubAnalyzer.core.models.errors import FileOperationError
from GithubAnalyzer.core.models.file import FileInfo, FileType, FileFilterConfig, FilePattern
from GithubAnalyzer.core.services.file_service import FileService

@pytest.fixture
def test_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory with test files.
    
    Returns:
        Path to temporary test directory.
    """
    # Create test files
    (tmp_path / "test.py").write_text("print('hello')")
    (tmp_path / "test.txt").write_text("hello")
    (tmp_path / "test.bin").write_bytes(b'\x00\x01\x02\x03')
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.py").write_text("def test(): pass")
    
    yield tmp_path

@pytest.fixture
def file_service() -> FileService:
    """Create a FileService instance."""
    return FileService()

def test_get_file_info(file_service: FileService, test_dir: Path) -> None:
    """Test getting file information."""
    file_path = test_dir / "test.py"
    info = file_service.get_file_info(file_path)
    
    assert isinstance(info, FileInfo)
    assert info.path == file_path
    assert info.file_type == FileType.PYTHON
    assert not info.is_binary
    assert info.size > 0

def test_list_files(file_service: FileService, test_dir: Path) -> None:
    """Test listing files in directory."""
    files = file_service.list_files(test_dir)
    
    assert len(files) == 4  # Including nested file
    assert any(f.path.name == "test.py" for f in files)
    assert any(f.path.name == "nested.py" for f in files)

def test_binary_detection(file_service: FileService, test_dir: Path) -> None:
    """Test binary file detection."""
    binary_info = file_service.get_file_info(test_dir / "test.bin")
    text_info = file_service.get_file_info(test_dir / "test.txt")
    
    assert binary_info.is_binary
    assert not text_info.is_binary

def test_file_filtering(file_service: FileService, test_dir: Path) -> None:
    """Test file filtering."""
    config = FileFilterConfig(
        include_patterns=[FilePattern("*.py")],
        exclude_patterns=[FilePattern("test_*.py")],
        max_size=1024 * 1024,  # 1MB
        allowed_types={FileType.PYTHON}
    )
    
    service_with_filter = FileService(config)
    files = service_with_filter.list_files(test_dir)
    
    assert len(files) == 2  # Only .py files
    assert all(f.file_type == FileType.PYTHON for f in files)

def test_error_handling(file_service: FileService) -> None:
    """Test error handling."""
    with pytest.raises(FileOperationError):
        file_service.get_file_info(Path("nonexistent.txt")) 