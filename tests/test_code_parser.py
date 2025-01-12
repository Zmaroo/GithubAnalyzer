import pytest
from GithubAnalyzer.core.services import ParserService
from GithubAnalyzer.core.models import TreeSitterNode, ParseResult

def test_parser_initialization():
    parser = ParserService()
    assert parser is not None
    assert parser.tree_sitter is not None

def test_parse_python_file(code_parser, sample_python_file):
    result = code_parser.parse_file(str(sample_python_file))
    
    assert result.success
    assert result.ast is not None
    assert result.tree_sitter_node is not None
    assert not result.errors
    
    # Check semantic information
    semantic = result.semantic
    assert len(semantic["functions"]) == 2  # hello and method
    assert len(semantic["classes"]) == 1    # TestClass

def test_parse_nonexistent_file():
    parser = ParserService()
    result = parser.parse_file("nonexistent.py")
    assert not result.success
    assert "File not found" in result.errors[0]

def test_parse_unsupported_extension(tmp_path):
    test_file = tmp_path / "test.unsupported"
    test_file.write_text("Some content")
    
    parser = ParserService()
    result = parser.parse_file(str(test_file))
    assert "error" in result
    assert "No parser for extension" in result["error"] 

def test_parse_javascript_file(code_parser, sample_js_file):
    result = code_parser.parse_file(str(sample_js_file))
    
    assert "error" not in result
    semantic = result["semantic"]
    assert len(semantic["functions"]) == 3  # hello, constructor, method
    assert len(semantic["classes"]) == 1    # TestClass

def test_syntax_error_detection(tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text("""
def broken_function(
    print("Missing closing parenthesis"
""")
    
    parser = ParserService()
    result = parser.parse_file(str(test_file))
    
    assert "errors" in result
    assert len(result["errors"]) > 0
    assert result["errors"][0]["type"] == "syntax_error"

def test_multiple_language_support(tmp_path):
    extensions = ['.py', '.js', '.java', '.cpp', '.go']
    for ext in extensions:
        test_file = tmp_path / f"test{ext}"
        test_file.write_text("// Test content")
        
        parser = ParserService()
        result = parser.parse_file(str(test_file))
        
        assert "error" not in result
        assert "tree" in result
        assert "syntax" in result 

def test_error_context(code_parser, tmp_path):
    """Test error context extraction"""
    test_file = tmp_path / "test.py"
    test_file.write_text("""
def broken_function(x:
    return x  # Missing closing parenthesis
""")
    
    result = code_parser.parse_file(str(test_file))
    assert "errors" in result
    error = result["errors"][0]
    assert "context" in error
    assert "previous_valid" in error["context"]
    assert "expected_symbols" in error["context"]

def test_semantic_extraction(code_parser, sample_python_file):
    """Test semantic information extraction"""
    result = code_parser.parse_file(str(sample_python_file))
    semantic = result["semantic"]
    
    # Check docstrings were captured
    docs = semantic["documentation"]
    assert any("Say hello" in doc["text"] for doc in docs)
    assert any("A test class" in doc["text"] for doc in docs)
    
    # Check function definitions
    funcs = semantic["functions"]
    assert any(func["text"] == "hello" for func in funcs)
    assert any(func["text"] == "method" for func in funcs)

def test_node_conversion(code_parser, sample_python_file):
    """Test AST node conversion"""
    result = code_parser.parse_file(str(sample_python_file))
    root_node = result["root_node"]
    
    assert isinstance(root_node, TreeSitterNode)
    assert hasattr(root_node, "type")
    assert hasattr(root_node, "text")
    assert hasattr(root_node, "start_point")
    assert hasattr(root_node, "end_point")
    assert hasattr(root_node, "children") 