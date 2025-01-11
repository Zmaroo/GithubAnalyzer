import pytest
from pathlib import Path

@pytest.fixture
def sample_python_file(tmp_path):
    """Create a sample Python file for testing"""
    file_path = tmp_path / "test.py"
    file_path.write_text("""
def hello():
    '''Say hello'''
    print("Hello, World!")
    
class TestClass:
    '''A test class'''
    def method(self):
        '''A test method'''
        pass
""")
    return file_path

@pytest.fixture
def sample_js_file(tmp_path):
    """Create a sample JavaScript file for testing"""
    file_path = tmp_path / "test.js"
    file_path.write_text("""
function hello() {
    console.log("Hello");
}

class TestClass {
    constructor() {}
    method() {}
}
""")
    return file_path

@pytest.fixture
def code_parser():
    """Create a CodeParser instance"""
    from GithubAnalyzer.core.code_parser import CodeParser
    return CodeParser() 

@pytest.fixture
def sample_error_file(tmp_path):
    """Create a file with syntax errors"""
    file_path = tmp_path / "error.py"
    file_path.write_text("""
def broken(x:
    print("Missing parenthesis"
class Incomplete:
""")
    return file_path

@pytest.fixture
def sample_complex_file(tmp_path):
    """Create a more complex Python file"""
    file_path = tmp_path / "complex.py"
    file_path.write_text('''
"""Module docstring"""
from typing import List, Optional

class BaseClass:
    """Base class docstring"""
    def __init__(self):
        pass

class ComplexClass(BaseClass):
    """Complex class docstring"""
    def method(self, x: int) -> List[str]:
        """Method docstring"""
        return [str(x)]

def complex_function(a: int, b: Optional[str] = None) -> bool:
    """Complex function docstring"""
    return bool(a and b)
''')
    return file_path 