"""Test suite for repository processing flow."""
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, Any
import pytest
from unittest.mock import patch, MagicMock

from tree_sitter import Parser, Language, Tree
from tree_sitter_language_pack import get_binding, get_language, get_parser
from GithubAnalyzer.services.core.repo_processor import RepoProcessor
from GithubAnalyzer.services.core.file_service import FileService
from GithubAnalyzer.services.analysis.parsers.language_service import LanguageService
from GithubAnalyzer.services.analysis.parsers.query_service import TreeSitterQueryHandler
from GithubAnalyzer.services.analysis.parsers.custom_parsers import get_custom_parser
from GithubAnalyzer.utils.logging import get_logger

# Set up basic logging for tests
logger = get_logger(__name__)

@pytest.fixture
def sample_repo():
    """Create a temporary repository with sample files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir)
        
        # Create Python file
        with open(repo_dir / "main.py", "w") as f:
            f.write('''def hello():
    print("Hello, World!")

class TestClass:
    def test_method(self):
        hello()
''')
        
        # Create JavaScript file
        with open(repo_dir / "app.js", "w") as f:
            f.write('''function greet(name) {
    return `Hello, ${name}!`;
}

class UserService {
    constructor() {
        this.users = [];
    }
    
    addUser(user) {
        this.users.push(user);
    }
}

// Anonymous function
const handler = function(event) {
    console.log(event);
};

// Arrow function
const process = (data) => {
    return data.map(x => x * 2);  // Nested arrow function
};
''')

        # Create TypeScript file
        with open(repo_dir / "types.ts", "w") as f:
            f.write('''interface User {
    id: number;
    name: string;
}

class UserManager {
    private users: User[] = [];
    
    addUser(user: User): void {
        this.users.push(user);
    }

    // Anonymous function as property
    private process = function(data: any): void {
        console.log(data);
    }

    // Arrow function as property
    private transform = (item: any): any => {
        return item;
    }
}
''')

        # Create Go file
        with open(repo_dir / "server.go", "w") as f:
            f.write('''package main

import "fmt"

func main() {
    fmt.Println("Hello from Go!")
}
''')

        # Create Java file
        with open(repo_dir / "Service.java", "w") as f:
            f.write('''public class Service {
    public static void main(String[] args) {
        System.out.println("Hello from Java!");
    }
}
''')

        # Create .env file
        with open(repo_dir / ".env", "w") as f:
            f.write('''DB_HOST=localhost
DB_PORT=5432
DB_NAME=testdb
''')

        # Create requirements.txt file
        with open(repo_dir / "requirements.txt", "w") as f:
            f.write('''pytest>=7.0.0
tree-sitter>=0.20.0
''')

        yield repo_dir

def test_repo_processing_flow(sample_repo, python_parser_with_logging):
    """Test the complete repository processing flow."""
    repo_processor = RepoProcessor()
    file_service = FileService()
    
    # 1. Test language detection
    python_file = sample_repo / "main.py"
    js_file = sample_repo / "app.js"
    ts_file = sample_repo / "types.ts"
    go_file = sample_repo / "server.go"
    java_file = sample_repo / "Service.java"
    env_file = sample_repo / ".env"
    requirements_file = sample_repo / "requirements.txt"
    
    # Check Python file detection
    python_info = file_service._detect_language(python_file)
    assert python_info == "python"
    
    # Check JavaScript file detection
    js_info = file_service._detect_language(js_file)
    assert js_info == "javascript"
    
    # Check TypeScript file detection
    ts_info = file_service._detect_language(ts_file)
    assert ts_info == "typescript"
    
    # Check Go file detection
    go_info = file_service._detect_language(go_file)
    assert go_info == "go"
    
    # Check Java file detection
    java_info = file_service._detect_language(java_file)
    assert java_info == "java"
    
    # Check .env file detection - should use custom parser
    env_info = file_service._detect_language(env_file)
    assert env_info == "env"  # Not "properties" from tree-sitter
    
    # Check requirements.txt detection - should use custom parser
    req_info = file_service._detect_language(requirements_file)
    assert req_info == "requirements"  # Not from tree-sitter
    
    # 2. Test custom parser integration
    with open(env_file) as f:
        env_content = f.read()
    env_parser = get_custom_parser(str(env_file))
    env_ast = env_parser.parse(env_content)
    assert env_ast is not None
    assert "DB_HOST" in env_ast
    
    # 3. Test tree-sitter parsing for each language
    # Python
    with open(python_file) as f:
        content = f.read()
    tree = python_parser_with_logging.parse(bytes(content, "utf8"))
    assert tree is not None
    assert not tree.root_node.has_error
    
    # JavaScript
    js_parser = get_parser("javascript")
    with open(js_file) as f:
        content = f.read()
    js_tree = js_parser.parse(bytes(content, "utf8"))
    assert js_tree is not None
    assert not js_tree.root_node.has_error
    
    # TypeScript
    ts_parser = get_parser("typescript")
    with open(ts_file) as f:
        content = f.read()
    ts_tree = ts_parser.parse(bytes(content, "utf8"))
    assert ts_tree is not None
    assert not ts_tree.root_node.has_error
    
    # Go
    go_parser = get_parser("go")
    with open(go_file) as f:
        content = f.read()
    go_tree = go_parser.parse(bytes(content, "utf8"))
    assert go_tree is not None
    assert not go_tree.root_node.has_error
    
    # Java
    java_parser = get_parser("java")
    with open(java_file) as f:
        content = f.read()
    java_tree = java_parser.parse(bytes(content, "utf8"))
    assert java_tree is not None
    assert not java_tree.root_node.has_error
    
    # 4. Test query handling for each language
    # Python
    query_handler = TreeSitterQueryHandler(language=tree.language, language_name="python")
    functions = query_handler.find_functions(tree.root_node)
    named_functions = [f for f in functions if f['is_named']]
    assert len(named_functions) == 2  # hello() and test_method()
    function_names = [f['function.name'].text.decode('utf-8') for f in named_functions]
    assert 'hello' in function_names
    assert 'test_method' in function_names
    
    # JavaScript
    js_query_handler = TreeSitterQueryHandler(language=js_tree.language, language_name="javascript")
    js_functions = js_query_handler.find_functions(js_tree.root_node)
    
    # Test named functions
    named_js_functions = [f for f in js_functions if f['is_named']]
    assert len(named_js_functions) >= 2  # greet() and UserService methods
    js_function_names = [f['function.name'].text.decode('utf-8') for f in named_js_functions]
    assert 'greet' in js_function_names
    assert 'addUser' in js_function_names
    
    # Test anonymous functions
    anon_js_functions = [f for f in js_functions if not f['is_named']]
    assert len(anon_js_functions) >= 3  # handler function, process arrow function, and nested arrow function
    
    # TypeScript
    ts_query_handler = TreeSitterQueryHandler(language=ts_tree.language, language_name="typescript")
    ts_functions = ts_query_handler.find_functions(ts_tree.root_node)
    
    # Test named functions
    named_ts_functions = [f for f in ts_functions if f['is_named']]
    assert len(named_ts_functions) == 3  # addUser method, process field, transform field
    ts_function_names = [f['function.name'].text.decode('utf-8') for f in named_ts_functions]
    assert set(ts_function_names) == {'addUser', 'process', 'transform'}
    
    # Test anonymous functions
    anon_ts_functions = [f for f in ts_functions if not f['is_named']]
    assert len(anon_ts_functions) == 3  # process arrow function, nested map arrow function, transform function expression
    
    # Total function count
    assert len(ts_functions) == 6  # Total of all named and anonymous functions
    
    # Go
    go_query_handler = TreeSitterQueryHandler(language=go_tree.language, language_name="go")
    go_functions = go_query_handler.find_functions(go_tree.root_node)
    named_go_functions = [f for f in go_functions if f['is_named']]
    assert len(named_go_functions) >= 1  # main function
    go_function_names = [f['function.name'].text.decode('utf-8') for f in named_go_functions]
    assert 'main' in go_function_names
    
    # Java
    java_query_handler = TreeSitterQueryHandler(language=java_tree.language, language_name="java")
    java_functions = java_query_handler.find_functions(java_tree.root_node)
    named_java_functions = [f for f in java_functions if f['is_named']]
    assert len(named_java_functions) >= 1  # main method
    java_function_names = [f['function.name'].text.decode('utf-8') for f in named_java_functions]
    assert 'main' in java_function_names
    
    # 5. Test complete repo processing
    files = file_service.get_repository_files(sample_repo, repo_id=1)  # Use test repo_id 1
    assert len(files) > 0
    
    # Process each file and verify expected results
    results = {}
    for file_info in files:
        result = repo_processor._process_file(file_info)
        results[file_info.path.name] = result

    # Verify expected successful parses
    assert results["main.py"] is not None
    assert results["main.py"].language == "python"
    assert results["main.py"].syntax_valid == True
    assert results["main.py"].ast_data != {}

    assert results["app.js"] is not None
    assert results["app.js"].language == "javascript"
    assert results["app.js"].syntax_valid == True
    assert results["app.js"].ast_data != {}

    assert results["types.ts"] is not None
    assert results["types.ts"].language == "typescript"
    assert results["types.ts"].syntax_valid == True
    assert results["types.ts"].ast_data != {}

    assert results["server.go"] is not None
    assert results["server.go"].language == "go"
    assert results["server.go"].syntax_valid == True
    assert results["server.go"].ast_data != {}

    assert results["Service.java"] is not None
    assert results["Service.java"].language == "java"
    assert results["Service.java"].syntax_valid == True
    assert results["Service.java"].ast_data != {}

    assert results[".env"] is not None
    assert results[".env"].language == "env"
    assert results[".env"].syntax_valid == True
    assert results[".env"].ast_data != {}

    assert results["requirements.txt"] is not None
    assert results["requirements.txt"].language == "requirements"
    assert results["requirements.txt"].syntax_valid == True
    assert results["requirements.txt"].ast_data != {}

def test_tree_sitter_parsing(python_parser_with_logging):
    """Test tree-sitter parsing functionality."""
    # Parse some code with potential issues
    code = """
    def broken_function(
        print("Missing closing parenthesis"
    """
    
    tree = python_parser_with_logging.parse(bytes(code, "utf8"))
    assert tree.root_node.has_error
    
    # Test valid code
    valid_code = """
def valid_function():
    return "Hello"
"""
    tree = python_parser_with_logging.parse(bytes(valid_code, "utf8"))
    assert not tree.root_node.has_error

def test_query_optimization(python_parser_with_logging):
    """Test query optimization functionality."""
    # Create query handler
    code = """
def test_function():
    x = 1
    y = 2
    return x + y
"""
    tree = python_parser_with_logging.parse(bytes(code, "utf8"))
    
    # Create query handler with the correct language and language name
    query_handler = TreeSitterQueryHandler(language=tree.language, language_name="python")
    
    # Find functions
    functions = query_handler.find_functions(tree.root_node)
    assert len(functions) == 1
    assert functions[0]['function.name'].text.decode() == 'test_function' 