"""Tests for FileService."""
import pytest
from pathlib import Path

from src.GithubAnalyzer.core.models.errors import FileOperationError
from src.GithubAnalyzer.core.models.file import FileInfo, FileType, FileFilterConfig
from src.GithubAnalyzer.core.services.file_service import FileService 