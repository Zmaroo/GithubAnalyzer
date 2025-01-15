"""Tests for TreeSitterParser functionality."""

from pathlib import Path
from typing import Dict, List, Generator
import pytest
from tree_sitter import Node, Tree, TreeCursor

from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.models.analysis.ast import ParseResult
from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser
from GithubAnalyzer.config.language_config import TREE_SITTER_LANGUAGES
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

@pytest.fixture
def parser() -> Generator[TreeSitterParser, None, None]:
    """Create a TreeSitterParser instance with all supported languages."""
    parser = TreeSitterParser()
    # Start with core languages that we know work
    core_languages = ["python", "javascript", "typescript"]
    parser.initialize(core_languages)
    yield parser
    parser.cleanup()

# Add a new fixture for testing specific languages
@pytest.fixture
def full_parser() -> Generator[TreeSitterParser, None, None]:
    """Create a TreeSitterParser instance for testing specific languages."""
    parser = TreeSitterParser()
    try:
        parser.initialize(TREE_SITTER_LANGUAGES)
    except ParserError as e:
        pytest.skip(f"Skipping full language tests: {e}")
    yield parser
    parser.cleanup()

# Basic Functionality Tests
def test_basic_parsing(parser: TreeSitterParser) -> None:
    """Test basic parsing functionality."""
    test_cases = {
        "python": "def test(): pass",
        "javascript": "function test() { }",
        "typescript": "function test(): void { }",
    }
    
    for lang, code in test_cases.items():
        result = parser.parse(code, lang)
        assert isinstance(result, ParseResult)
        assert result.is_valid
        assert result.node_count > 0
        assert result.metadata["root_type"] == "module" or result.metadata["root_type"] == "program"

def test_error_recovery(parser: TreeSitterParser) -> None:
    """Test parser error recovery capabilities."""
    # Test cases with syntax errors for different languages
    test_cases = {
        "python": """def valid_function():
    return 42

def invalid_function)  # Syntax error here
    print("Hello")

def another_valid():  # Should still find this
    pass""",
        
        "javascript": """function valid() {
    return 42;
}

function invalid( {  # Syntax error here
    console.log("error");
}

function alsoValid() {  # Should still find this
    return true;
}""",
    }
    
    for lang, content in test_cases.items():
        logger.info(f"Testing error recovery for {lang}")
        result = parser.parse(content, lang)
        
        # Should get a parse tree even with errors
        assert result.ast is not None
        assert not result.is_valid
        assert len(result.errors) > 0
        
        # Should find valid functions despite errors
        functions = result.metadata["analysis"]["functions"]
        logger.info(f"Found functions: {functions}")
        
        if lang == "python":
            assert "valid_function" in functions
            assert "another_valid" in functions
            assert functions["valid_function"]["start"] == 0
            assert functions["another_valid"]["start"] == 6
        elif lang == "javascript":
            assert "valid" in functions
            assert "alsoValid" in functions
            assert functions["valid"]["start"] == 0
            assert functions["alsoValid"]["start"] == 8

def test_language_support(full_parser: TreeSitterParser) -> None:
    """Test support for all configured languages."""
    test_cases = {
        # Core languages
        "python": "def test(): pass",
        "javascript": "function test() { }",
        "typescript": "function test(): void { }",
        # System languages
        "java": "class Test { void test() { } }",
        "cpp": "int main() { return 0; }",
        "c": "int main() { return 0; }",
        "c-sharp": "class Program { static void Main() { } }",
        "go": "func main() { }",
        # Scripting languages
        "ruby": "def test\n  puts 'test'\nend",
        "php": "<?php function test() { }",
        "lua": "function test() return 42 end",
        "groovy": "def test() { println 'test' }",
        "scala": "object Test { def main(args: Array[String]): Unit = {} }",
        "kotlin": "fun test() = 42",
        # Web technologies
        "html": "<div>test</div>",
        "css": "body { color: red; }",
        "json": '{"test": true}',
        "yaml": "test: value",
        "xml": "<root><test>value</test></root>",
        "markdown": "# Test\n\nHello",
        # Scientific/Engineering
        "matlab": "function y = test(x)\ny = x + 1;\nend",
        "cuda": "__global__ void test(int* x) { }",
        "arduino": "void setup() { }",
        "toml": 'test = "value"',
        # Query languages
        "sql": "SELECT * FROM test;"
    }
    
    # Verify we're testing all configured languages
    untested_languages = set(TREE_SITTER_LANGUAGES) - set(test_cases.keys())
    if untested_languages:
        pytest.skip(f"Missing test cases for languages: {untested_languages}")
    
    # Test each language
    for lang, code in test_cases.items():
        try:
            result = full_parser.parse(code, lang)
            assert isinstance(result, ParseResult)
            assert result.ast is not None
            print(f"Successfully parsed {lang}")
        except Exception as e:
            pytest.fail(f"Failed to parse {lang}: {e}")

def test_encoding_handling(parser: TreeSitterParser) -> None:
    """Test handling of different text encodings."""
    test_cases = {
        "ascii": 'print("Hello!")',
        "unicode": 'print("Hello, 世界! 🌍")',
        "mixed": 'def test(): return "Hello, мир! 🌍"',
    }
    
    for case_name, content in test_cases.items():
        result = parser.parse(content, "python")
        assert result.is_valid
        assert result.metadata["encoding"] == "utf8"

def test_tree_traversal(parser: TreeSitterParser) -> None:
    """Test tree traversal and node access."""
    content = """
def example():
    if True:
        return 42
    """
    result = parser.parse(content, "python")
    assert result.is_valid
    
    # Test cursor traversal
    cursor = result.ast.walk()
    assert cursor.node.type == "module"
    
    # Test node field access
    function_node = None
    for node in cursor.node.children:
        if node.type == "function_definition":
            function_node = node
            break
    
    assert function_node is not None
    name_node = function_node.child_by_field_name("name")
    assert name_node is not None
    assert name_node.text.decode("utf8") == "example"

def test_syntax_error_detection(parser: TreeSitterParser) -> None:
    """Test detection and handling of syntax errors."""
    error_cases = [
        ("python", "def test:", "ERROR"),  # Missing parentheses
        ("javascript", "function test( {", "ERROR"),  # Missing closing parenthesis
        ("python", "def test():\nprint('test')", None),  # Valid but unusual indentation
        ("javascript", "console.log('test'", "ERROR"),  # Missing closing parenthesis
    ]
    
    for lang, code, expected_error in error_cases:
        result = parser.parse(code, lang)
        if expected_error == "ERROR":
            assert not result.is_valid
            assert len(result.errors) > 0
        else:
            assert result.is_valid
            assert len(result.errors) == 0

def test_metadata_completeness(parser: TreeSitterParser) -> None:
    """Test completeness of parse result metadata."""
    content = "x = 42"
    result = parser.parse(content, "python")
    
    assert result.metadata["encoding"] == "utf8"
    assert result.metadata["raw_content"] == content
    assert result.metadata["root_type"] == "module"
    assert "analysis" in result.metadata
    assert isinstance(result.metadata["analysis"], dict)
    assert "errors" in result.metadata["analysis"] 

def test_language_variants(parser: TreeSitterParser) -> None:
    """Test support for language variants (TSX, JSX, etc.)."""
    variant_cases = {
        "typescript": {
            "tsx": """
                function Component(): JSX.Element {
                    return <div>Hello</div>;
                }
            """,
            "standard": "function test(): void { }"
        },
        # JavaScript handles JSX natively in its parser
        "javascript": """
            function Component() {
                return <div>Hello</div>;
            }
        """
    }
    
    for lang, variants in variant_cases.items():
        if isinstance(variants, dict):
            for variant_type, code in variants.items():
                try:
                    result = parser.parse(code, lang)
                    assert isinstance(result, ParseResult)
                    assert result.ast is not None
                    print(f"Successfully parsed {lang} ({variant_type})")
                except Exception as e:
                    pytest.fail(f"Failed to parse {lang} {variant_type}: {e}")
        else:
            try:
                result = parser.parse(variants, lang)
                assert isinstance(result, ParseResult)
                assert result.ast is not None
                print(f"Successfully parsed {lang}")
            except Exception as e:
                pytest.fail(f"Failed to parse {lang}: {e}") 