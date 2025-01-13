"""Basic tree-sitter functionality tests"""
import pytest
from tree_sitter import Parser, Language
import tree_sitter_python
import tree_sitter_javascript

@pytest.fixture
def sample_python_code():
    return """
def hello(name: str) -> str:
    return f"Hello, {name}!"
"""

@pytest.fixture
def sample_js_code():
    return """
function hello(name) {
    return `Hello, ${name}!`;
}
"""

def test_basic_python_parsing():
    """Test basic Python parsing with tree-sitter"""
    # Initialize Python language
    py_language = Language(tree_sitter_python.language())
    parser = Parser()
    parser.set_language(py_language)
    
    code = """
def hello():
    print("Hello!")
"""
    tree = parser.parse(bytes(code, 'utf8'))
    assert tree is not None
    assert tree.root_node.type == 'module'
    
    # Find the function definition
    function_node = next(
        node for node in tree.root_node.children 
        if node.type == 'function_definition'
    )
    assert function_node.type == 'function_definition'
    assert function_node.child_by_field_name('name').text.decode('utf8') == 'hello'

def test_multiple_languages():
    """Test parsing multiple languages"""
    parser = Parser()
    
    # Initialize languages
    py_language = Language(tree_sitter_python.language())
    js_language = Language(tree_sitter_javascript.language())
    
    # Test Python
    parser.set_language(py_language)
    python_code = "def test(): pass"
    tree = parser.parse(bytes(python_code, 'utf8'))
    assert tree.root_node.type == 'module'
    
    # Test JavaScript
    parser.set_language(js_language)
    js_code = "function test() {}"
    tree = parser.parse(bytes(js_code, 'utf8'))
    assert tree.root_node.type == 'program'

def test_language_initialization():
    """Test language initialization"""
    # Test Python language
    py_language = Language(tree_sitter_python.language())
    assert py_language is not None
    
    # Test JavaScript language
    js_language = Language(tree_sitter_javascript.language())
    assert js_language is not None
    
    # Create parser and test both languages
    parser = Parser()
    
    # Python
    parser.set_language(py_language)
    tree = parser.parse(b"def test(): pass")
    assert tree.root_node.type == 'module'
    
    # JavaScript
    parser.set_language(js_language)
    tree = parser.parse(b"function test() {}")
    assert tree.root_node.type == 'program' 