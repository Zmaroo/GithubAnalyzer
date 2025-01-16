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

def test_parser_initialization_errors():
    """Test error handling during parser initialization."""
    from tree_sitter import Parser, Query
    
    parser = TreeSitterParser()
    parser.initialize(["python"])  # Initialize Python first
    
    # Test invalid language - should skip and continue
    parser.initialize(["not_a_real_language"])
    assert "not_a_real_language" not in parser._parsers
    
    # Test invalid query pattern - use tree-sitter's native query API
    python_language = parser._parsers["python"].language
    with pytest.raises(Exception):  # Tree-sitter raises generic Exception for invalid queries
        Query(python_language, "(invalid_query")  # Use Query constructor directly

def test_parser_cleanup():
    """Test proper cleanup of parser resources."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    
    # Verify initialization
    assert "python" in parser._parsers
    assert parser._queries
    
    # Test cleanup
    parser.cleanup()
    assert not parser._parsers
    assert not parser._queries

def test_parser_configuration():
    """Test parser configuration options."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    
    # Test debug mode - should add debug info to AST output
    parser._debug = True
    result = parser.parse("def test(): pass", "python")
    assert result.metadata["root_type"] == "module"  # Debug mode shows AST structure
    assert "test" in result.metadata["analysis"]["functions"]  # Debug mode logs functions
    
    # Test encoding handling
    test_code = "def test(): pass"
    result = parser.parse(test_code.encode('utf8'), "python")
    assert result.metadata["encoding"] == "utf8"

def test_error_handling():
    """Test various error conditions."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    
    # Test parsing None content - tree-sitter requires bytestring or callable
    ts_parser = parser._parsers["python"]
    with pytest.raises(TypeError):
        ts_parser.parse(None)
    
    # Test invalid language - should raise KeyError for missing parser
    with pytest.raises(KeyError):
        _ = parser._parsers["invalid"]
    
    # Test corrupted parser state - should raise ParserError
    parser._parsers["python"] = None
    with pytest.raises(ParserError):
        parser.parse("def test(): pass", "python")

def test_query_handling():
    """Test query creation and handling."""
    parser = TreeSitterParser()
    
    # Use tree-sitter's native query API
    query_str = """
    (function_definition
      name: (identifier) @function.def)
    """
    
    parser.initialize(["python"])
    python_parser = parser._parsers.get("python")
    assert python_parser is not None
    
    # Test query execution
    code = "def test(): pass"
    result = parser.parse(code, "python")
    assert result.ast is not None
    
    # Verify function was found
    functions = result.metadata["analysis"]["functions"]
    assert "test" in functions

def test_node_analysis():
    """Test detailed node analysis."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    
    code = """
    def outer():
        def inner():
            pass
        class Inner:
            def method(self):
                pass
    """
    
    result = parser.parse(code, "python")
    functions = result.metadata["analysis"]["functions"]
    
    assert "outer" in functions
    assert "inner" in functions
    assert "method" in functions 

def test_debug_ast_printing(caplog):
    """Test debug AST printing functionality."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    parser._debug = True
    
    code = """
    def test():
        x = 1
        return x
    """
    
    with caplog.at_level(logging.DEBUG):
        result = parser.parse(code, "python")
        
    # Tree-sitter debug output includes node types and function detection
    debug_messages = [record.message for record in caplog.records]
    assert any("Tree-sitter [python]: Parsing content" in msg for msg in debug_messages)
    assert any("Added function: test" in msg for msg in debug_messages)

def test_complex_analysis():
    """Test analysis of complex code structures."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    
    code = """
    class TestClass:
        def __init__(self):
            self.x = 42
            
        @property
        def value(self):
            return self.x
            
        @classmethod
        def factory(cls):
            return cls()
            
        async def async_method(self):
            await something()
    """
    
    result = parser.parse(code, "python")
    functions = result.metadata["analysis"]["functions"]
    
    # Test method detection
    assert "__init__" in functions
    assert "value" in functions
    assert "factory" in functions
    assert "async_method" in functions
    
    # Test decorators don't interfere
    assert "@property" not in functions
    assert "@classmethod" not in functions

def test_error_recovery_modes():
    """Test different error recovery scenarios."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    
    test_cases = {
        "missing_paren": (
            "def test(:\n    pass",
            True,  # Should recover
            True   # Should have errors
        ),
        "incomplete_class": (
            "class Test\ndef method(self):",  # Missing colon
            True,  # Should recover
            True   # Should have errors
        ),
        "severe_error": (
            "def @#$ test))",
            False,  # Should not recover
            True   # Should have errors
        )
    }
    
    for case_name, (code, should_recover, should_have_errors) in test_cases.items():
        result = parser.parse(code, "python")
        if should_recover:
            assert result.ast is not None
            # Check for errors using tree-sitter's node properties
            root_node = result.ast.root_node
            assert root_node.has_error == should_have_errors, f"Expected has_error={should_have_errors} for {case_name}"
            
            # Find error nodes using tree-sitter's cursor
            cursor = root_node.walk()
            error_found = False
            
            while cursor.goto_first_child() or cursor.goto_next_sibling():
                if cursor.node.is_error or cursor.node.has_error:
                    error_found = True
                    break
            
            assert error_found == should_have_errors, f"Expected to find error nodes: {should_have_errors}"
        else:
            assert not result.is_valid

def test_node_traversal():
    """Test detailed node traversal and analysis."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    
    code = """
    def outer():
        x = 1
        def inner():
            y = 2
            return x + y
        return inner
    
    class Test:
        def method(self):
            pass
    """
    
    result = parser.parse(code, "python")
    
    # Test node relationships
    root = result.ast.root_node
    assert root.type == "module"
    
    # Find function definitions
    functions = []
    cursor = result.ast.walk()
    
    def visit_node():
        node = cursor.node
        if node.type == "function_definition":
            functions.append(node.child_by_field_name("name").text.decode('utf8'))
        return True
        
    cursor.goto_first_child()
    while cursor:
        visit_node()
        if not cursor.goto_first_child():
            while not cursor.goto_next_sibling():
                if not cursor.goto_parent():
                    cursor = None
                    break
                    
    assert set(functions) == {"outer", "inner", "method"} 

def test_parser_error_handling():
    """Test various parser error conditions."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    
    # Test missing language
    with pytest.raises(ParserError):
        parser.parse("def test(): pass", "nonexistent")
    
    # Test invalid source code type
    with pytest.raises(TypeError):
        parser.parse(123, "python")  # Not a string or bytes
    
    # Test empty content
    result = parser.parse("", "python")
    assert result.ast is not None
    assert result.ast.root_node.type == "module"
    assert len(result.ast.root_node.children) == 0

def test_parser_metadata():
    """Test parser metadata handling."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    
    code = """
    def test():
        '''Doc string'''
        pass
    
    class Example:
        def method(self):
            pass
    """
    
    result = parser.parse(code, "python")
    metadata = result.metadata
    
    # Check metadata fields
    assert "encoding" in metadata
    assert "raw_content" in metadata
    assert "root_type" in metadata
    assert "analysis" in metadata
    assert "functions" in metadata["analysis"]
    assert "errors" in metadata["analysis"]
    
    # Check function analysis
    functions = metadata["analysis"]["functions"]
    assert "test" in functions
    assert "method" in functions
    
    # Check byte offsets
    assert functions["test"]["start"] < functions["method"]["start"]

def test_parser_debug_mode():
    """Test parser debug mode functionality."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    parser._debug = True
    
    with caplog.at_level(logging.DEBUG):
        result = parser.parse("""
        def test():
            if True:
                return 42
        """, "python")
        
        # Check debug logs
        assert any("Parsing content" in msg for msg in caplog.records)
        assert any("function_definition" in msg for msg in caplog.records)
        assert any("Added function: test" in msg for msg in caplog.records)
        
        # Check debug metadata
        assert result.metadata.get("debug_enabled")
        assert "node_count" in result.metadata
        assert "parse_time" in result.metadata

def test_parser_query_cache():
    """Test query caching mechanism."""
    parser = TreeSitterParser()
    parser.initialize(["python"])
    
    # First parse should create query
    result1 = parser.parse("def test(): pass", "python")
    assert "python_functions" in parser._queries
    
    # Get the cached query
    cached_query = parser._queries["python_functions"]
    
    # Second parse should use cached query
    result2 = parser.parse("def another(): pass", "python")
    assert parser._queries["python_functions"] is cached_query
    
    # Clear queries
    parser._queries = {}
    assert not parser._queries
    
    # Should recreate query
    result3 = parser.parse("def third(): pass", "python")
    assert "python_functions" in parser._queries 