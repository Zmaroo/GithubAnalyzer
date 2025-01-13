import pytest
from pathlib import Path
from GithubAnalyzer.parsers.custom import (
    PythonParser,
    JavaScriptParser,
    TypeScriptParser
)
from GithubAnalyzer.core.custom_parsers import (
    BuildSystemParser,
    CIConfigParser,
    ProjectConfigParser,
    LicenseParser,
    MetadataParser,
    initialize_parsers
)

@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for testing"""
    files = {
        'requirements.txt': """
            numpy>=1.20.0
            pandas==1.4.0
            # Comment line
            requests>=2.26.0  # Inline comment
        """,
        
        '.gitignore': """
            # Python
            __pycache__/
            *.py[cod]
            !important.pyc
        """,
        
        'LICENSE': """
            MIT License
            
            Copyright (c) 2024 Test Project
            
            Permission is hereby granted, free of charge...
        """,
        
        'AUTHORS': """
            MAINTAINERS
            John Doe <john@example.com>
            
            CONTRIBUTORS
            Jane Smith <jane@example.com>
        """,
        
        '.gitlab-ci.yml': """
stages:
  - test
  - build

test:
  stage: test
  script:
    - pytest
"""
    }
    
    # Create test files
    for filename, content in files.items():
        file_path = tmp_path / filename
        file_path.write_text(content.strip())
        
    return tmp_path

def test_build_system_parser(sample_files):
    parser = BuildSystemParser()
    filepath = sample_files / 'requirements.txt'
    parser.set_current_file(str(filepath))
    content = filepath.read_text()
    
    result = parser.parse(content)
    assert 'requirements' in result
    assert len(result['requirements']) == 3
    
    # Check package parsing
    numpy_req = next(r for r in result['requirements'] if r['package'] == 'numpy')
    assert numpy_req['constraint'] == '>='
    assert numpy_req['version'] == '1.20.0'

def test_project_config_parser(sample_files):
    parser = ProjectConfigParser()
    filepath = sample_files / '.gitignore'
    parser.set_current_file(str(filepath))
    content = filepath.read_text()
    
    result = parser.parse(content)
    assert 'exclude' in result
    assert 'include' in result
    assert '*.py[cod]' in result['exclude']
    assert 'important.pyc' in result['include']

def test_license_parser(sample_files):
    parser = LicenseParser()
    filepath = sample_files / 'LICENSE'
    parser.set_current_file(str(filepath))
    content = filepath.read_text()
    
    result = parser.parse(content)
    assert result['type'] == 'MIT'
    assert result['metadata']['copyright_year'] == '2024'
    assert 'Test Project' in result['metadata']['copyright_holder']

def test_metadata_parser(sample_files):
    parser = MetadataParser()
    filepath = sample_files / 'AUTHORS'
    parser.set_current_file(str(filepath))
    content = filepath.read_text()
    
    result = parser.parse(content)
    sections = result['sections']
    assert len(sections) == 2
    assert sections[0]['title'] == 'MAINTAINERS'
    assert 'John Doe' in ' '.join(sections[0]['content'])

def test_ci_config_parser(sample_files):
    parser = CIConfigParser()
    filepath = sample_files / '.gitlab-ci.yml'
    parser.set_current_file(str(filepath))
    content = filepath.read_text()
    
    result = parser.parse(content)
    assert 'stages' in result
    assert 'test' in result['stages']
    assert 'jobs' in result
    assert 'test' in result['jobs']
    assert result['jobs']['test']['stage'] == 'test'

def test_parser_registry():
    registry = initialize_parsers()
    
    # Test extension mapping
    assert registry.get_parser('requirements.txt').__class__ == BuildSystemParser
    assert registry.get_parser('.gitignore').__class__ == ProjectConfigParser
    assert registry.get_parser('LICENSE').__class__ == LicenseParser
    
    # Test tree-sitter detection
    assert registry._is_tree_sitter_extension('.py') is True
    assert registry._is_tree_sitter_extension('.gitignore') is False

@pytest.mark.parametrize("parser_type,content,expected_error", [
    (CIConfigParser, "invalid: :\nyaml", "Invalid YAML"),
    (ProjectConfigParser, "malformed xml<>", "Invalid XML"),
    (CIConfigParser, "", "Empty file"),
    (LicenseParser, "some random text", "Not a valid license file"),
])
def test_parser_error_handling(parser_type, content, expected_error):
    parser = parser_type()
    # Set appropriate file extension based on parser type
    if parser_type == CIConfigParser:
        parser.set_current_file("test.yml")
    elif parser_type == ProjectConfigParser:
        parser.set_current_file("test.xml")
    else:
        parser.set_current_file(f"test.{parser_type.__name__}")
    
    result = parser.parse(content)
    assert 'error' in result
    assert expected_error in result['error'] 