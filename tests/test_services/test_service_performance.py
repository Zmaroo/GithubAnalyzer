import pytest
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from GithubAnalyzer.core.registry import BusinessTools
from GithubAnalyzer.core.models import (
    ModuleInfo,
    AnalysisResult,
    RepositoryState
)

@pytest.fixture
def business_tools():
    """Create properly initialized business tools"""
    tools = BusinessTools.create()
    yield tools
    tools.database_service.cleanup()

@pytest.fixture
def large_project(tmp_path):
    """Create a large project structure for performance testing"""
    project_dir = tmp_path / "large_project"
    project_dir.mkdir()
    
    # Create many Python files
    for i in range(100):
        module_dir = project_dir / f"module_{i}"
        module_dir.mkdir()
        
        # Each module has multiple files
        for j in range(5):
            (module_dir / f"file_{j}.py").write_text(f"""
# Module {i}, File {j}
from typing import List, Optional

class TestClass_{i}_{j}:
    \"\"\"Test class docstring\"\"\"
    def __init__(self):
        self.value = {i * j}
    
    def method_{j}(self, x: int) -> str:
        \"\"\"Test method\"\"\"
        return str(x + self.value)

def helper_function_{j}(data: List[str]) -> Optional[str]:
    \"\"\"Helper function\"\"\"
    return data[0] if data else None
""")
    
    return project_dir

def test_parallel_analysis(business_tools, large_project):
    """Test parallel analysis of multiple files"""
    start_time = time.time()
    
    # Get all Python files
    python_files = list(large_project.rglob("*.py"))
    assert len(python_files) == 500  # 100 modules * 5 files
    
    # Analyze files in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(business_tools.analyzer_service.analyze_file, str(f))
            for f in python_files
        ]
        results = [f.result() for f in futures]
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Verify results
    assert len(results) == 500
    assert all(isinstance(r, ModuleInfo) for r in results)
    
    # Log performance metrics
    print(f"\nParallel analysis of 500 files took {duration:.2f} seconds")
    print(f"Average time per file: {(duration/500)*1000:.2f}ms")

def test_cache_performance(business_tools, large_project):
    """Test caching performance with large dataset"""
    # First analysis without cache
    start_time = time.time()
    result1 = business_tools.analyzer_service.analyze_repository(
        str(large_project)
    )
    first_duration = time.time() - start_time
    
    # Cache the results
    business_tools.database_service.cache_analysis_result(
        "large_project:analysis",
        result1
    )
    
    # Second analysis with cache
    start_time = time.time()
    result2 = business_tools.analyzer_service.analyze_repository(
        str(large_project)
    )
    second_duration = time.time() - start_time
    
    # Verify cache improved performance
    assert second_duration < first_duration
    print(f"\nFirst analysis: {first_duration:.2f}s")
    print(f"Cached analysis: {second_duration:.2f}s")
    print(f"Cache speedup: {first_duration/second_duration:.1f}x")

def test_memory_usage(business_tools, large_project):
    """Test memory usage during large project analysis"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Analyze large project
    result = business_tools.analyzer_service.analyze_repository(
        str(large_project)
    )
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    print(f"\nMemory usage increased by {memory_increase:.1f}MB")
    print(f"Memory per file: {(memory_increase/500):.2f}MB")
    
    # Memory usage should be reasonable
    assert memory_increase < 1000  # Less than 1GB increase

def test_database_scaling(business_tools, large_project):
    """Test database performance with increasing data"""
    import random
    
    # Create many repository states
    start_time = time.time()
    for i in range(100):
        state = RepositoryState(
            url=f"test_url_{i}",
            status="analyzing",
            progress=random.random(),
            current_operation=f"Operation {i}"
        )
        business_tools.database_service.store_repository_state(state)
    
    # Bulk retrieve states
    states = [
        business_tools.database_service.get_repository_state(f"test_url_{i}")
        for i in range(100)
    ]
    end_time = time.time()
    
    assert len(states) == 100
    print(f"\nDatabase operations for 100 states: {(end_time-start_time)*1000:.2f}ms")
    print(f"Average time per operation: {((end_time-start_time)*1000/100):.2f}ms")

@pytest.mark.slow
def test_long_running_analysis(business_tools, large_project):
    """Test stability of long-running analysis"""
    # Simulate long-running analysis with progress updates
    state = RepositoryState(
        url="long_running_test",
        status="analyzing",
        progress=0.0
    )
    
    for i in range(10):
        state.progress = i / 10
        business_tools.database_service.store_repository_state(state)
        
        # Analyze a subset of files
        files = list(large_project.rglob("*.py"))[i*50:(i+1)*50]
        for file in files:
            module_info = business_tools.analyzer_service.analyze_file(str(file))
            assert module_info is not None
        
        time.sleep(0.1)  # Simulate work
    
    state.status = "completed"
    state.progress = 1.0
    business_tools.database_service.store_repository_state(state)
    
    final_state = business_tools.database_service.get_repository_state(
        "long_running_test"
    )
    assert final_state.status == "completed"
    assert final_state.progress == 1.0 