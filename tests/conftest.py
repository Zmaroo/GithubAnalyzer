"""Test configuration and fixtures"""
import pytest
from pathlib import Path
from GithubAnalyzer.core.registry import AnalysisToolRegistry
from GithubAnalyzer.core.models.database import DatabaseConfig

@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "database": DatabaseConfig(
            pg_conn_string="postgresql://test:test@localhost:5432/test_db",
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="test",
            redis_host="localhost",
            redis_port=6379,
            use_cache=True
        ),
        "max_file_size": 1024 * 1024,  # 1MB
        "batch_size": 10
    }

@pytest.fixture
def registry():
    """Create registry instance"""
    registry = AnalysisToolRegistry.create()
    yield registry
    registry.database_service.cleanup()

@pytest.fixture
def sample_repo(tmp_path):
    """Create sample repository structure"""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    # Create Python module
    module_dir = repo_dir / "src"
    module_dir.mkdir()
    
    # Add sample files
    (module_dir / "main.py").write_text("""
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")
    
    (module_dir / "utils.py").write_text("""
def helper_function(x: int) -> str:
    return str(x * 2)
""")
    
    # Add configuration
    (repo_dir / "config.yaml").write_text("""
app:
  name: test-app
  version: 1.0.0
""")
    
    return repo_dir

@pytest.fixture
def complex_repo(tmp_path):
    """Create complex repository structure"""
    repo_dir = tmp_path / "complex_repo"
    repo_dir.mkdir()
    
    # Create multiple modules with dependencies
    src_dir = repo_dir / "src"
    src_dir.mkdir()
    
    # Add complex module structure
    # ... (add more complex file structures)
    
    return repo_dir 

@pytest.fixture
def common_ops(registry):
    """Get common operations"""
    return registry.get_common_operations() 