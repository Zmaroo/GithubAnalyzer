import pytest
from pathlib import Path
from GithubAnalyzer.core.services import ParserService

def test_parser_initialization():
    parser = ParserService()
    assert parser is not None
    parser._initialize()
    assert len(parser.parsers) > 0

def test_parse_python_file(code_parser, sample_python_file):
    content = sample_python_file.read_text()
    result = code_parser.parse_file(str(sample_python_file), content)
    
    assert result["success"]
    assert "ast" in result
    assert not result.get("errors", [])
    
    # Check semantic information
    semantic = result.get("semantic", {})
    assert len(semantic.get("functions", [])) >= 1  # example_function
    assert len(semantic.get("classes", [])) >= 1    # ExampleClass

def test_parse_nonexistent_file():
    parser = ParserService()
    parser._initialize()
    with pytest.raises(FileNotFoundError):
        parser.parse_file("nonexistent.py", "")

def test_parse_unsupported_extension(tmp_path):
    test_file = tmp_path / "test.unsupported"
    test_file.write_text("Some content")
    
    parser = ParserService()
    parser._initialize()
    result = parser.parse_file(str(test_file), test_file.read_text())
    assert not result["success"]
    assert "No suitable parser found" in result["errors"][0]

def test_parse_javascript_file(code_parser, sample_js_file):
    content = sample_js_file.read_text()
    result = code_parser.parse_file(str(sample_js_file), content)
    
    assert result["success"]
    semantic = result.get("semantic", {})
    assert len(semantic.get("functions", [])) >= 1  # exampleFunction
    assert len(semantic.get("classes", [])) >= 1    # ExampleClass

def test_syntax_error_detection(tmp_path):
    test_file = tmp_path / "test.py"
    content = """
def broken_function(
    print("Missing closing parenthesis"
"""
    test_file.write_text(content)
    
    parser = ParserService()
    parser._initialize()
    result = parser.parse_file(str(test_file), content)
    
    assert not result["success"]
    assert len(result.get("errors", [])) > 0
    assert "syntax" in result.get("errors", [])[0].lower()

def test_multiple_language_support(tmp_path):
    extensions = ['.py', '.js', '.java', '.cpp', '.go']
    content = "// Test content"
    
    parser = ParserService()
    parser._initialize()
    
    for ext in extensions:
        test_file = tmp_path / f"test{ext}"
        test_file.write_text(content)
        result = parser.parse_file(str(test_file), content)
        assert "success" in result

def test_error_context(code_parser, tmp_path):
    """Test error context extraction"""
    content = """
def broken_function(x:
    return x  # Missing closing parenthesis
"""
    test_file = tmp_path / "test.py"
    test_file.write_text(content)
    
    result = code_parser.parse_file(str(test_file), content)
    assert not result["success"]
    assert len(result.get("errors", [])) > 0
    error = result["errors"][0]
    assert isinstance(error, str)  # Error messages are strings

def test_semantic_extraction(code_parser, sample_python_file):
    """Test semantic information extraction"""
    content = sample_python_file.read_text()
    result = code_parser.parse_file(str(sample_python_file), content)
    
    assert result["success"]
    semantic = result.get("semantic", {})
    
    # Check function and class definitions
    functions = semantic.get("functions", [])
    classes = semantic.get("classes", [])
    
    assert any("example_function" in str(func) for func in functions)
    assert any("ExampleClass" in str(cls) for cls in classes)

def test_node_conversion(code_parser, sample_python_file):
    """Test AST node conversion"""
    content = sample_python_file.read_text()
    result = code_parser.parse_file(str(sample_python_file), content)
    
    assert result["success"]
    assert "ast" in result
    ast = result["ast"]
    
    # Basic AST structure checks
    assert isinstance(ast, dict)
    assert "type" in ast
    assert "children" in ast 