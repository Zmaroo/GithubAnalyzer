import pytest
from pathlib import Path
from GithubAnalyzer.core.parsers.custom import (
    ConfigParser,
    DocumentationParser,
    LicenseParser
)

@pytest.fixture
def sample_config_file(tmp_path):
    """Create a sample config file"""
    file_path = tmp_path / "config.yaml"
    file_path.write_text("""
app:
  name: TestApp
  version: 1.0.0
settings:
  debug: true
  port: 8080
""")
    return file_path

@pytest.fixture
def sample_doc_file(tmp_path):
    """Create a sample markdown file"""
    file_path = tmp_path / "README.md"
    file_path.write_text("""
# Project Title

## Description
This is a test project.

## Installation
1. Clone the repo
2. Install dependencies
""")
    return file_path

@pytest.fixture
def sample_license_file(tmp_path):
    """Create a sample license file"""
    file_path = tmp_path / "LICENSE"
    file_path.write_text("""
MIT License

Permission is hereby granted, free of charge...
""")
    return file_path

def test_config_parser(sample_config_file):
    parser = ConfigParser()
    assert parser.can_parse(str(sample_config_file))
    
    with open(sample_config_file) as f:
        result = parser.parse(f.read())
    
    assert result.success
    assert result.semantic['type'] == 'config'
    assert result.semantic['content']['app']['name'] == 'TestApp'

def test_doc_parser(sample_doc_file):
    parser = DocumentationParser()
    assert parser.can_parse(str(sample_doc_file))
    
    with open(sample_doc_file) as f:
        result = parser.parse(f.read())
    
    assert result.success
    assert result.semantic['type'] == 'documentation'
    assert len(result.semantic['sections']) == 3  # Title, Description, Installation

def test_license_parser(sample_license_file):
    parser = LicenseParser()
    assert parser.can_parse(str(sample_license_file))
    
    with open(sample_license_file) as f:
        result = parser.parse(f.read())
    
    assert result.success
    assert result.semantic['type'] == 'license'
    assert result.semantic['license_type'] == 'MIT' 