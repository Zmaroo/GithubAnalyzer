"""Tests for FileService."""

import pytest
from pathlib import Path
import tempfile
import os
from typing import Generator

from src.GithubAnalyzer.core.services.file_service import FileService
from src.GithubAnalyzer.core.models.file import FileInfo, FileFilterConfig
from src.GithubAnalyzer.core.models.errors import FileOperationError, LanguageError

@pytest.fixture
def file_service() -> FileService:
    """Create a FileService instance."""
    return FileService()

@pytest.fixture
def test_dir() -> Generator[Path, None, None]:
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        dir_path = Path(temp_dir)
        
        # Code files
        (dir_path / "test.py").write_text("def test(): pass")
        (dir_path / "main.cpp").write_text("int main() { return 0; }")
        (dir_path / "script.js").write_text("function test() {}")
        
        # Binary file
        with open(dir_path / "binary.bin", "wb") as f:
            f.write(b"\x00\x01\x02\x03")
            
        # Nested directory
        nested = dir_path / "nested"
        nested.mkdir()
        (nested / "nested.py").write_text("# Nested file")
        
        yield dir_path

def test_list_files_basic(file_service: FileService, test_dir: Path):
    """Test basic file listing functionality."""
    files = file_service.list_files(test_dir)
    assert len(files) == 5
    languages = {f.language for f in files}
    assert languages == {"python", "cpp", "javascript", "unknown"}

def test_list_files_with_filter(file_service: FileService, test_dir: Path):
    """Test listing files with filters."""
    # Clean up any existing files
    for file in test_dir.rglob('*'):
        if file.is_file():
            file.unlink()
    for dir in reversed(list(test_dir.rglob('*'))):
        if dir.is_dir():
            dir.rmdir()

    # Create test files
    test_files = {
        'test.py': 'print("hello")',
        'main.cpp': 'int main() { return 0; }',
        'script.js': 'console.log("hello")',
        'config.yaml': 'key: value',
        'README.md': '# Title'
    }
    for name, content in test_files.items():
        path = test_dir / name
        path.write_text(content)

    # Test filtering by language
    config = FileFilterConfig(include_languages=['python'])
    files = file_service.list_files(test_dir, config)
    assert len(files) == 1
    assert files[0].path.name == 'test.py'

    # Test filtering by extension patterns
    config = FileFilterConfig(include_paths=['*.py', '*.js'])
    files = file_service.list_files(test_dir, config)
    assert len(files) == 2
    assert {f.path.name for f in files} == {'test.py', 'script.js'}

    # Test filtering by exclude patterns
    config = FileFilterConfig(exclude_paths=['*.md', '*.yaml'])
    files = file_service.list_files(test_dir, config)
    assert len(files) == 3
    assert {f.path.name for f in files} == {'test.py', 'main.cpp', 'script.js'}

def test_list_files_invalid_path(file_service: FileService):
    """Test listing files with invalid path."""
    with pytest.raises(FileOperationError, match="Path does not exist"):
        file_service.list_files(Path("/nonexistent"))

def test_list_files_not_dir(file_service: FileService, test_dir: Path):
    """Test listing files with a file path."""
    file_path = test_dir / "test.py"
    with pytest.raises(FileOperationError, match="Path is not a directory"):
        file_service.list_files(file_path)

def test_create_file_info(file_service: FileService, test_dir: Path):
    """Test creating FileInfo objects."""
    py_file = test_dir / "test.py"
    file_info = file_service._create_file_info(py_file)
    assert file_info.language == "python"
    assert file_info.metadata["extension"] == ".py"
    assert not file_info.metadata["is_binary"]
    assert file_info.metadata["size"] > 0

def test_detect_language(file_service: FileService, test_dir: Path):
    """Test language detection."""
    # Known language
    assert file_service._detect_language(Path("test.py")) == "python"
    assert file_service._detect_language(Path("test.cpp")) == "cpp"
    
    # Unknown language
    assert file_service._detect_language(Path("test.xyz")) == "unknown"

def test_get_file_info_success(file_service: FileService, test_dir: Path):
    """Test getting file info successfully."""
    file_info = file_service.get_file_info(test_dir / "test.py")
    assert file_info.language == "python"
    assert isinstance(file_info.metadata, dict)
    assert "size" in file_info.metadata
    assert "extension" in file_info.metadata
    assert "is_binary" in file_info.metadata

def test_get_file_info_not_found(file_service: FileService):
    """Test getting file info for non-existent file."""
    with pytest.raises(FileOperationError, match="File not found"):
        file_service.get_file_info(Path("nonexistent.py"))

def test_get_file_info_unsupported_language(file_service: FileService, test_dir: Path):
    """Test getting file info for unsupported language."""
    unsupported = test_dir / "test.xyz"
    unsupported.write_text("test")
    with pytest.raises(LanguageError, match="Language not supported"):
        file_service.get_file_info(unsupported)

def test_is_binary(file_service: FileService, test_dir: Path):
    """Test binary file detection."""
    # Text file
    assert not file_service._is_binary(test_dir / "test.py")
    
    # Binary file
    assert file_service._is_binary(test_dir / "binary.bin")

def test_read_file(file_service: FileService, test_dir: Path):
    """Test reading file contents."""
    content = file_service.read_file(test_dir / "test.py")
    assert content == "def test(): pass"

def test_read_file_not_found(file_service: FileService):
    """Test reading non-existent file."""
    with pytest.raises(Exception):
        file_service.read_file(Path("nonexistent.py"))

def test_test_file_type(file_service: FileService, test_dir: Path):
    """Test file type checking."""
    file_info = file_service.get_file_info(test_dir / "test.py")
    assert file_service.test_file_type(file_info, "python")
    assert not file_service.test_file_type(file_info, "javascript") 