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

@pytest.fixture
def invalid_yaml_file(tmp_path):
    """Create an invalid YAML file"""
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text("""
app:
  name: TestApp
  version: 1.0.0
    invalid_indent:
- broken list
""")
    return file_path

@pytest.fixture
def complex_doc_file(tmp_path):
    """Create a more complex markdown file"""
    file_path = tmp_path / "CONTRIBUTING.md"
    file_path.write_text("""
# Contributing Guide

## Code Style
Please follow PEP 8.

## Testing
- Write unit tests
- Ensure coverage > 80%

### Running Tests
```bash
pytest
```

## Pull Requests
1. Fork the repo
2. Create feature branch
3. Submit PR
""")
    return file_path

@pytest.fixture
def apache_license_file(tmp_path):
    """Create an Apache license file"""
    file_path = tmp_path / "LICENSE"
    file_path.write_text("""
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/
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

def test_config_parser_invalid_yaml(invalid_yaml_file):
    """Test handling of invalid YAML"""
    parser = ConfigParser()
    with open(invalid_yaml_file) as f:
        result = parser.parse(f.read())
    
    assert not result.success
    assert len(result.errors) > 0

def test_doc_parser_complex(complex_doc_file):
    """Test parsing of complex markdown"""
    parser = DocumentationParser()
    with open(complex_doc_file) as f:
        result = parser.parse(f.read())
    
    assert result.success
    assert result.semantic['type'] == 'documentation'
    sections = result.semantic['sections']
    assert len(sections) > 3
    assert any(s['title'] == 'Code Style' for s in sections)
    assert any(s['title'] == 'Running Tests' for s in sections)

def test_license_parser_apache(apache_license_file):
    """Test Apache license detection"""
    parser = LicenseParser()
    with open(apache_license_file) as f:
        result = parser.parse(f.read())
    
    assert result.success
    assert result.semantic['license_type'] == 'Apache-2.0'
    summary = result.semantic['summary']
    assert 'patent-use' in summary['permissions']
    assert 'include-notice' in summary['conditions']

def test_parser_nonexistent_file():
    """Test handling of nonexistent files"""
    parsers = [ConfigParser(), DocumentationParser(), LicenseParser()]
    
    for parser in parsers:
        assert not parser.can_parse('nonexistent.txt')
        parser.set_current_file('nonexistent.txt')
        result = parser.parse('')
        assert not result.success
        assert len(result.errors) > 0

def test_parser_empty_content():
    """Test handling of empty content"""
    parsers = [ConfigParser(), DocumentationParser(), LicenseParser()]
    
    for parser in parsers:
        result = parser.parse('')
        assert not result.success or result.semantic.get('content') == ''

def test_config_parser_different_formats(tmp_path):
    """Test parsing different config formats"""
    formats = {
        'json': ('config.json', '{"app": {"name": "TestApp"}}'),
        'toml': ('pyproject.toml', '[tool.poetry]\nname = "TestApp"'),
        'ini': ('setup.cfg', '[metadata]\nname = TestApp')
    }
    
    parser = ConfigParser()
    for fmt, (filename, content) in formats.items():
        file_path = tmp_path / filename
        file_path.write_text(content)
        
        assert parser.can_parse(str(file_path))
        with open(file_path) as f:
            result = parser.parse(f.read())
        
        assert result.success
        assert result.semantic['type'] == 'config'
        assert result.semantic['format'] == fmt 