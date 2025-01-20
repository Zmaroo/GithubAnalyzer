"""Performance tests for the TreeSitterParser."""

import resource
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psutil
import pytest

from GithubAnalyzer.models.core.errors import ParseError
from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser


@pytest.fixture
def parser():
    """Create a TreeSitterParser instance."""
    parser = TreeSitterParser()
    parser.initialize()
    return parser


def test_parsing_speed(parser):
    """Test parsing speed for different file sizes."""
    sizes = [1000, 10000, 100000]
    times = []

    for size in sizes:
        code = "def test():\n" + "    pass\n" * size

        start_time = time.time()
        result = parser.parse(code, "python")
        end_time = time.time()

        assert result["syntax_valid"]
        times.append(end_time - start_time)

        # Parsing time should scale roughly linearly
        if len(times) > 1:
            ratio = times[-1] / times[-2]
            assert ratio < 15  # Should not be exponential


def test_memory_usage(parser):
    """Test memory usage during parsing."""
    process = psutil.Process()
    initial_memory = process.memory_info().rss

    # Parse a large file
    code = "def test():\n" + "    pass\n" * 10000
    result = parser.parse(code, "python")
    assert result["syntax_valid"]

    peak_memory = process.memory_info().rss
    memory_increase = peak_memory - initial_memory

    # Memory usage should be reasonable (less than 100MB increase)
    assert memory_increase < 100 * 1024 * 1024


def test_concurrent_parsing_performance(parser):
    """Test performance of concurrent parsing."""
    code = "def test():\n    pass\n" * 1000
    num_iterations = 100

    def parse_code():
        for _ in range(num_iterations):
            result = parser.parse(code, "python")
            assert result["syntax_valid"]

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(parse_code) for _ in range(4)]
        for future in futures:
            future.result()
    end_time = time.time()

    total_time = end_time - start_time
    operations_per_second = (num_iterations * 4) / total_time

    # Should achieve at least 100 operations per second
    assert operations_per_second > 100


def test_resource_limits(parser):
    """Test parsing with resource limits."""
    # Set CPU time limit to 30 seconds
    soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
    resource.setrlimit(resource.RLIMIT_CPU, (30, hard))

    # Set memory limit to 1GB
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, hard))

    code = "def test():\n" + "    pass\n" * 10000
    result = parser.parse(code, "python")
    assert result["syntax_valid"]
