"""Test configuration and fixtures"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from GithubAnalyzer.core.registry import AnalysisToolRegistry
from GithubAnalyzer.core.models.database import DatabaseConfig, DatabaseConnection
from GithubAnalyzer.core.parsers.tree_sitter import TreeSitterParser
from GithubAnalyzer.core.services.parser_service import ParserService

@pytest.fixture(scope="session")
def mock_db_connection():
    """Create mock database connections"""
    conn = DatabaseConnection()
    
    # Mock PostgreSQL connection
    pg_mock = MagicMock()
    pg_mock.closed = False
    pg_mock.status = 1  # Connected
    conn.pg_conn = pg_mock
    
    # Mock Neo4j connection
    neo4j_mock = MagicMock()
    neo4j_mock.closed = False
    neo4j_mock.verify_connectivity.return_value = True
    conn.neo4j_conn = neo4j_mock
    
    # Mock Redis connection
    redis_mock = MagicMock()
    redis_mock.ping.return_value = True
    conn.redis_conn = redis_mock
    
    conn.is_connected = True
    return conn

@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "database": DatabaseConfig(
            pg_conn_string="mock://test:test@localhost:5432/test_db",
            neo4j_uri="mock://localhost:7687",
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
def registry(mock_db_connection, monkeypatch):
    """Create registry instance with mocked database connections"""
    def mock_init_postgres(self):
        self.connection = mock_db_connection
        self.pg_conn = mock_db_connection.pg_conn
        self.is_connected = True
        
    def mock_init_neo4j(self):
        self.neo4j_conn = mock_db_connection.neo4j_conn
        
    def mock_init_redis(self):
        self.redis_conn = mock_db_connection.redis_conn
    
    # Patch database initialization
    monkeypatch.setattr('GithubAnalyzer.core.services.database_service.DatabaseService._init_postgres', mock_init_postgres)
    monkeypatch.setattr('GithubAnalyzer.core.services.database_service.DatabaseService._init_neo4j', mock_init_neo4j)
    monkeypatch.setattr('GithubAnalyzer.core.services.database_service.DatabaseService._init_redis', mock_init_redis)
    
    # Patch database operations to return success
    monkeypatch.setattr('GithubAnalyzer.core.services.database_service.DatabaseService.store_repository_info', lambda *args, **kwargs: True)
    monkeypatch.setattr('GithubAnalyzer.core.services.database_service.DatabaseService.store_repository_state', lambda *args, **kwargs: True)
    monkeypatch.setattr('GithubAnalyzer.core.services.database_service.DatabaseService.store_graph_data', lambda *args, **kwargs: True)
    monkeypatch.setattr('GithubAnalyzer.core.services.database_service.DatabaseService.cache_set', lambda *args, **kwargs: True)
    monkeypatch.setattr('GithubAnalyzer.core.services.database_service.DatabaseService.cache_get', lambda *args, **kwargs: None)
    
    registry = AnalysisToolRegistry.create()
    yield registry
    registry.database_service.cleanup()

@pytest.fixture
def code_parser(registry):
    """Create code parser instance"""
    return registry.parser_service

@pytest.fixture
def sample_python_file(tmp_path):
    """Create a sample Python file for testing"""
    file_path = tmp_path / "test.py"
    file_path.write_text("""
def example_function(x: int) -> str:
    return f"Value: {x}"

class ExampleClass:
    def method(self):
        return 42
""")
    return file_path

@pytest.fixture
def sample_js_file(tmp_path):
    """Create a sample JavaScript file for testing"""
    file_path = tmp_path / "test.js"
    file_path.write_text("""
function exampleFunction(x) {
    return `Value: ${x}`;
}

class ExampleClass {
    method() {
        return 42;
    }
}
""")
    return file_path

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
    (src_dir / "models.py").write_text("""
from dataclasses import dataclass
from typing import List

@dataclass
class User:
    name: str
    email: str
    
@dataclass
class Project:
    name: str
    owner: User
    contributors: List[User]
""")
    
    (src_dir / "services.py").write_text("""
class ProjectService:
    def __init__(self):
        self.projects = {}
        
    def create_project(self, name: str, owner):
        self.projects[name] = {"owner": owner, "contributors": []}
""")
    
    return repo_dir 

@pytest.fixture
def common_ops(registry):
    """Get common operations"""
    return registry.get_common_operations() 