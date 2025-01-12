import pytest
import json
from datetime import datetime
from GithubAnalyzer.core.services import DatabaseService
from GithubAnalyzer.core.models.database import (
    RepositoryInfo,
    GraphNode,
    GraphRelationship,
    RepositoryState
)

@pytest.fixture
def database_service():
    """Create a database service instance"""
    service = DatabaseService()
    yield service
    service.cleanup()  # Cleanup after tests

@pytest.fixture
def sample_repo_info():
    """Create sample repository info"""
    return RepositoryInfo(
        name="test-repo",
        url="https://github.com/test/test-repo",
        local_path="/tmp/test-repo",
        last_analyzed=datetime.now().isoformat(),
        is_current=True,
        metadata={
            "language": "Python",
            "files": 42,
            "lines": 1000
        }
    )

@pytest.fixture
def sample_graph_data():
    """Create sample graph data"""
    # Create nodes
    module_node = GraphNode(
        id="module1",
        labels=["Module"],
        properties={"name": "main.py", "path": "/src/main.py"}
    )
    
    class_node = GraphNode(
        id="class1",
        labels=["Class"],
        properties={"name": "TestClass", "module": "main.py"}
    )
    
    # Create relationship
    contains_rel = GraphRelationship(
        type="CONTAINS",
        start_node=module_node,
        end_node=class_node,
        properties={"type": "class_def"}
    )
    
    return {
        "nodes": [module_node, class_node],
        "relationships": [contains_rel]
    }

def test_database_initialization(database_service):
    """Test database connections are initialized"""
    assert database_service.pg_conn is not None
    assert database_service.neo4j_conn is not None
    assert database_service.redis_client is not None

def test_store_repository_info(database_service, sample_repo_info):
    """Test storing repository information"""
    success = database_service.store_repository_info(sample_repo_info)
    assert success
    
    # Verify storage
    stored = database_service.get_repository_info(sample_repo_info.url)
    assert stored is not None
    assert stored.name == sample_repo_info.name
    assert stored.url == sample_repo_info.url

def test_store_graph_data(database_service, sample_graph_data):
    """Test storing graph data"""
    success = database_service.store_graph_data(
        sample_graph_data["nodes"],
        sample_graph_data["relationships"]
    )
    assert success

def test_cache_operations(database_service):
    """Test cache operations"""
    test_data = {"key": "value"}
    
    # Store in cache
    success = database_service.cache_analysis_result(
        "test_key",
        test_data,
        ttl=60
    )
    assert success
    
    # Retrieve from cache
    cached = database_service.get_cached_analysis("test_key")
    assert cached == test_data

def test_handle_connection_errors(monkeypatch):
    """Test handling of database connection errors"""
    def mock_init_postgres(*args, **kwargs):
        return None
        
    monkeypatch.setattr(
        "GithubAnalyzer.core.services.database_service.DatabaseService._init_postgres",
        mock_init_postgres
    )
    
    service = DatabaseService()
    assert service.pg_conn is None
    
    # Operations should fail gracefully
    result = service.store_repository_info(RepositoryInfo(
        name="test",
        url="test",
        local_path="test"
    ))
    assert not result

def test_cleanup(database_service):
    """Test cleanup of database connections"""
    database_service.cleanup()
    
    assert not database_service.pg_conn
    assert not database_service.neo4j_conn
    assert not database_service.redis_client

@pytest.mark.parametrize("data", [
    {"simple": "data"},
    {"nested": {"data": True}},
    ["list", "of", "items"],
    42,
    "string"
])
def test_cache_different_data_types(database_service, data):
    """Test caching different data types"""
    key = f"test_key_{type(data).__name__}"
    
    success = database_service.cache_analysis_result(key, data)
    assert success
    
    cached = database_service.get_cached_analysis(key)
    assert cached == data

def test_repository_state_updates(database_service):
    """Test repository state updates"""
    state = RepositoryState(
        url="https://github.com/test/repo",
        status="analyzing",
        last_update=datetime.now().timestamp(),
        progress=0.5,
        current_operation="Parsing files"
    )
    
    success = database_service.store_repository_state(state)
    assert success
    
    stored_state = database_service.get_repository_state(state.url)
    assert stored_state is not None
    assert stored_state.status == state.status
    assert stored_state.progress == state.progress 