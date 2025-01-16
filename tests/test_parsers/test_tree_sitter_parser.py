"""Tests for TreeSitterParser functionality."""

from pathlib import Path
from typing import Dict, List, Generator
import pytest
from tree_sitter import Node, Tree, TreeCursor
import logging

from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.models.analysis.ast import ParseResult
from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser
from GithubAnalyzer.config.language_config import TREE_SITTER_LANGUAGES
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

@pytest.fixture
def parser() -> Generator[TreeSitterParser, None, None]:
    """Create a TreeSitterParser instance with all supported languages."""
    parser = TreeSitterParser()
    # Start with core languages that we know work
    core_languages = ["python", "javascript", "typescript", "tsx"]
    parser.initialize(core_languages)
    yield parser
    parser.cleanup()

# Add a new fixture for testing specific languages
@pytest.fixture
def full_parser() -> Generator[TreeSitterParser, None, None]:
    """Create a TreeSitterParser instance for testing specific languages."""
    parser = TreeSitterParser()
    try:
        # Initialize all core languages
        core_languages = [
            "python", "javascript", "typescript", "tsx",
            "java", "cpp", "c", "go"  # Added system languages
        ]
        parser.initialize(core_languages)
        yield parser
    except Exception as e:
        pytest.skip(f"Skipping full language tests: {e}")
    finally:
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

def print_ast_structure(node: Node, level: int = 0) -> None:
    """Print AST structure for debugging."""
    indent = "  " * level
    print(f"{indent}{node.type}: {node.text.decode('utf8') if node.text else ''}")
    print(f"{indent}Start: {node.start_point}, End: {node.end_point}")
    print(f"{indent}Error: {node.has_error}, Missing: {node.is_missing}")
    
    for child in node.children:
        print_ast_structure(child, level + 1)

def test_error_recovery(parser: TreeSitterParser) -> None:
    """Test parser error recovery capabilities."""
    parser._debug = True  # Enable debugging
    
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
        
        if lang == "python":
            # Verify function names are found
            assert "valid_function" in functions
            assert "another_valid" in functions
            
            # Verify byte offsets match AST
            assert functions["valid_function"]["start"] == 0  # First function starts at byte 0
            assert functions["another_valid"]["start"] == 124  # def keyword starts at byte 124
            
            # Verify error recovery worked
            assert len(result.errors) > 0  # Should have caught the syntax error
            assert any("Syntax error" in err for err in result.errors)

def test_language_support(full_parser: TreeSitterParser) -> None:
    """Test support for all configured languages."""
    test_cases = {
        # Core languages
        "python": "def test(): pass",
        "javascript": "function test() { }",
        "typescript": "function test(): void { }",
        "tsx": """
            function Component(): JSX.Element {
                return <div>Hello</div>;
            }
            
            const Arrow = () => {
                return <span>Hi</span>;
            }
            
            class Example extends React.Component {
                handleClick = () => {}
                render() {
                    return <div>Click me</div>;
                }
            }
        """,
        # System languages
        "java": "class Test { void test() { } }",
        "cpp": "int main() { return 0; }",
        "c": "int main() { return 0; }",
        "go": "func main() { }"
    }
    
    # Test each language
    for lang, code in test_cases.items():
        try:
            result = full_parser.parse(code, lang)
            assert isinstance(result, ParseResult)
            assert result.ast is not None
            
            # Additional checks for TSX
            if lang == "tsx":
                functions = result.metadata["analysis"]["functions"]
                assert "Component" in functions, "Failed to detect function component"
                assert "Arrow" in functions, "Failed to detect arrow component"
                assert "handleClick" in functions, "Failed to detect class field"
                assert "render" in functions, "Failed to detect class method"
            
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

def test_tsx_support(full_parser: TreeSitterParser) -> None:
    """Test TSX-specific parsing capabilities."""
    full_parser._debug = True

    test_cases = {
        # Basic function component
        "function_component": """
            function Welcome(props: WelcomeProps): JSX.Element {
                return <h1>Hello, {props.name}</h1>;
            }
        """,

        # Arrow function component
        "arrow_component": """
            const Greeting = (props: GreetingProps): React.ReactNode => {
                return <div>Welcome back!</div>;
            }
        """,

        # Class component with methods
        "class_component": """
            class Counter extends React.Component {
                handleClick = () => {
                    this.setState({ count: this.state.count + 1 });
                }

                render(): ReactElement {
                    return <button onClick={this.handleClick}>{this.state.count}</button>;
                }
            }
        """,

        # Component with error
        "error_component": """
            function ErrorComponent(: ComponentProps) {  // Syntax error
                return <div>Error</div>;
            }

            const ValidComponent = () => {  // Should still find this
                return <span>Valid</span>;
            }
        """
    }

    for case_name, content in test_cases.items():
        logger.info(f"Testing TSX case: {case_name}")
        result = full_parser.parse(content, "tsx")

        # Basic validation
        assert result.ast is not None
        
        # Check function detection
        functions = result.metadata["analysis"]["functions"]
        
        if case_name == "function_component":
            assert "Welcome" in functions
        elif case_name == "arrow_component":
            assert "Greeting" in functions
        elif case_name == "class_component":
            assert "handleClick" in functions
        elif case_name == "error_component":
            assert "ValidComponent" in functions 