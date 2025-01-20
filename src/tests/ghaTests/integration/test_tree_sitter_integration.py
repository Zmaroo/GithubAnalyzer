"""Integration tests for the TreeSitterParser."""

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from GithubAnalyzer.models.core.errors import ParseError
from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser


@pytest.fixture
def parser():
    """Create a TreeSitterParser instance."""
    parser = TreeSitterParser()
    parser.initialize()
    return parser


@pytest.fixture
def test_files(tmp_path):
    """Create test files for different languages."""
    files = {}
    test_cases = {
        "test.py": """
def hello():
    print("Hello, World!")
    return 42
""",
        "test.js": """
function hello() {
    console.log("Hello, World!");
    return 42;
}
""",
        "test.cpp": """
int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
""",
        "test.java": """
class Test {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
""",
    }

    for filename, content in test_cases.items():
        file_path = tmp_path / filename
        file_path.write_text(content)
        files[filename] = file_path

    return files


def test_parallel_parsing(parser, test_files):
    """Test parsing multiple files in parallel."""

    def parse_file(file_path):
        return parser.parse_file(str(file_path))

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(parse_file, path) for path in test_files.values()]
        results = [future.result() for future in futures]

    for result in results:
        assert result["syntax_valid"]
        assert result["node_count"] > 0


def test_language_autodetection(parser):
    """Test automatic language detection from file extensions."""
    test_cases = {
        "test.py": "python",
        "main.js": "javascript",
        "style.css": "css",
        "config.yaml": "yaml",
        "data.json": "json",
        "script.sh": "bash",
        "code.cpp": "cpp",
        "app.java": "java",
        "test.rs": "rust",
        "index.html": "html",
    }

    for file_path, expected_lang in test_cases.items():
        detected = parser._get_language_for_file(file_path)
        assert detected == expected_lang


def test_batch_file_parsing(parser, test_files):
    """Test parsing multiple files in sequence."""
    for file_path in test_files.values():
        result = parser.parse_file(str(file_path))
        assert result["syntax_valid"]
        assert result["node_count"] > 0
        assert result["metadata"]["language"] == parser._get_language_for_file(
            str(file_path)
        )
