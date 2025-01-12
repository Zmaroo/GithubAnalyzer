"""Parser test fixtures"""
import pytest
from pathlib import Path

@pytest.fixture
def sample_python_file(tmp_path):
    """Create a sample Python file for testing"""
    file_path = tmp_path / "test.py"
    file_path.write_text("""
def hello(name: str) -> str:
    \"\"\"Say hello\"\"\"
    return f"Hello, {name}!"

class TestClass:
    \"\"\"A test class\"\"\"
    def method(self):
        return hello("World")
""")
    return file_path 