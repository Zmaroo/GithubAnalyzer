import pytest
from pathlib import Path
from GithubAnalyzer.core.services import ParserService
from GithubAnalyzer.core.models.base import ParseResult

@pytest.fixture
def parser_service():
    """Create a parser service instance"""
    return ParserService()

@pytest.fixture
def mixed_content_dir(tmp_path):
    """Create directory with mixed content types"""
    # Create Python file
    (tmp_path / "main.py").write_text("""
def hello():
    print("Hello, World!")
""")

    # Create config file
    (tmp_path / "config.yaml").write_text("""
app:
  name: TestApp
""")

    # Create documentation
    (tmp_path / "README.md").write_text("""
# Test Project
""")

    # Create license
    (tmp_path / "LICENSE").write_text("""
MIT License
""")

    return tmp_path

def test_parser_service_initialization(parser_service):
    """Test parser service initialization"""
    assert parser_service.tree_sitter is not None
    assert len(parser_service.custom_parsers) > 0
    assert len(parser_service.file_type_map) > 0

def test_parse_mixed_content(parser_service, mixed_content_dir):
    """Test parsing different file types"""
    for file_path in mixed_content_dir.iterdir():
        with open(file_path) as f:
            result = parser_service.parse_file(str(file_path), f.read())
        
        assert isinstance(result, ParseResult)
        assert result.success
        assert result.semantic.get('type') is not None

def test_parser_service_error_handling(parser_service, tmp_path):
    """Test error handling"""
    # Test nonexistent file
    result = parser_service.parse_file(str(tmp_path / "nonexistent.txt"), "")
    assert not result.success
    assert len(result.errors) > 0

    # Test unsupported file type
    unsupported = tmp_path / "test.unsupported"
    unsupported.write_text("test")
    result = parser_service.parse_file(str(unsupported), "test")
    assert not result.success
    assert "No parser available" in result.errors[0] 