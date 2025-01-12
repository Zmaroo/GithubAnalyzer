import pytest
import os
from pathlib import Path
from GithubAnalyzer.core.registry import AnalysisToolRegistry
from GithubAnalyzer.core.models import (
    RepositoryInfo,
    RepositoryState,
    GraphNode
)

@pytest.fixture
def common_ops(registry):
    """Get common operations interface"""
    return registry.get_common_operations()

@pytest.fixture
def malicious_project(tmp_path):
    """Create a project with potentially malicious content"""
    project_dir = tmp_path / "malicious_project"
    project_dir.mkdir()
    
    # File with SQL injection attempt
    (project_dir / "sql_injection.py").write_text("""
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}; DROP TABLE users;--"
    return execute_query(query)
""")
    
    # File with command injection
    (project_dir / "command_injection.py").write_text("""
import os
def process_file(filename):
    os.system(f"cat {filename} | grep 'secret'")  # Dangerous
""")
    
    # File with infinite recursion
    (project_dir / "infinite_recursion.py").write_text("""
def recursive_function(n):
    return recursive_function(n + 1)
""")
    
    # File attempting filesystem access
    (project_dir / "filesystem_access.py").write_text("""
import os
def delete_files():
    os.remove('/etc/passwd')  # Dangerous
""")
    
    return project_dir

def test_sql_injection_detection(common_ops, malicious_project):
    """Test detection of SQL injection vulnerabilities"""
    file_path = malicious_project / "sql_injection.py"
    module_info = common_ops.analyze_file(str(file_path))
    
    # Should detect and flag SQL injection risk
    assert module_info is not None
    assert any(
        'sql injection' in str(warning).lower() 
        for warning in module_info.warnings
    )

def test_command_injection_detection(common_ops, malicious_project):
    """Test detection of command injection vulnerabilities"""
    file_path = malicious_project / "command_injection.py"
    module_info = common_ops.analyze_file(str(file_path))
    
    # Should detect and flag command injection risk
    assert module_info is not None
    assert any(
        'command injection' in str(warning).lower() 
        for warning in module_info.warnings
    )

def test_infinite_recursion_handling(common_ops, malicious_project):
    """Test handling of potential infinite recursion"""
    file_path = malicious_project / "infinite_recursion.py"
    module_info = common_ops.analyze_file(str(file_path))
    
    # Should detect recursion risk
    assert module_info is not None
    assert any(
        'recursive' in str(warning).lower() 
        for warning in module_info.warnings
    )

def test_filesystem_access_detection(common_ops, malicious_project):
    """Test detection of dangerous filesystem operations"""
    file_path = malicious_project / "filesystem_access.py"
    module_info = common_ops.analyze_file(str(file_path))
    
    # Should detect filesystem risk
    assert module_info is not None
    assert any(
        'filesystem' in str(warning).lower() 
        for warning in module_info.warnings
    )

def test_path_traversal_prevention(common_ops, tmp_path):
    """Test prevention of path traversal attacks"""
    # Attempt path traversal
    malicious_paths = [
        "../../../etc/passwd",
        "..\\..\\Windows\\System32",
        "/etc/passwd",
        "C:\\Windows\\System32",
        "file:///etc/passwd",
        "http://evil.com/malicious.py"
    ]
    
    for path in malicious_paths:
        module_info = common_ops.analyze_file(path)
        assert module_info is None or not module_info.success

def test_large_file_handling(common_ops, tmp_path):
    """Test handling of unusually large files"""
    large_file = tmp_path / "large.py"
    
    # Create a 10MB Python file
    with open(large_file, 'w') as f:
        f.write('x = ' + '[0] * 1000000\n' * 100)
    
    # Should handle large file gracefully
    module_info = common_ops.analyze_file(str(large_file))
    assert module_info is not None
    assert 'file size' in str(module_info.warnings).lower()

def test_memory_limit_handling(common_ops, tmp_path):
    """Test handling of memory-intensive operations"""
    memory_hog = tmp_path / "memory_hog.py"
    memory_hog.write_text("""
# Attempt to create a huge list
huge_list = list(range(1000000000))
""")
    
    # Should handle memory-intensive file gracefully
    module_info = common_ops.analyze_file(str(memory_hog))
    assert module_info is not None
    assert 'memory usage' in str(module_info.warnings).lower()

def test_malformed_data_handling(common_ops):
    """Test handling of malformed data in database operations"""
    # Test malformed repository info
    malformed_info = RepositoryInfo(
        name="<script>alert('xss')</script>",
        url="javascript:alert('xss')",
        local_path="/etc/passwd",
        metadata={"huge": "x" * 1000000}  # Very large metadata
    )
    
    # Should sanitize and handle malformed data
    success = common_ops.database_service.store_repository_info(malformed_info)
    assert success
    
    stored = common_ops.database_service.get_repository_info(malformed_info.url)
    assert stored is not None
    assert "<script>" not in stored.name
    assert "javascript:" not in stored.url

def test_concurrent_access_handling(common_ops):
    """Test handling of concurrent database access"""
    from concurrent.futures import ThreadPoolExecutor
    import random
    
    def concurrent_operation(i):
        state = RepositoryState(
            url=f"concurrent_test_{i}",
            status="analyzing",
            progress=random.random()
        )
        return common_ops.database_service.store_repository_state(state)
    
    # Run many concurrent operations
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(concurrent_operation, range(100)))
    
    # All operations should complete successfully
    assert all(results)

def test_invalid_graph_data(common_ops):
    """Test handling of invalid graph data"""
    # Create invalid graph nodes
    invalid_nodes = [
        GraphNode(id="", labels=[], properties={}),  # Empty ID
        GraphNode(id="test", labels=["Invalid!@#$"], properties={}),  # Invalid label
        GraphNode(id="test", labels=["Test"], properties={"key": object()}),  # Invalid property
    ]
    
    # Should handle invalid data gracefully
    for node in invalid_nodes:
        result = common_ops.database_service.store_graph_data([node], [])
        assert not result 