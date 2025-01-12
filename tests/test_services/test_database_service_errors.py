import pytest
from GithubAnalyzer.core.services import DatabaseService
from GithubAnalyzer.core.models.database import RepositoryInfo, GraphNode

def test_handle_postgres_connection_error(monkeypatch):
    """Test handling PostgreSQL connection errors"""
    def mock_connect(*args, **kwargs):
        raise Exception("Connection failed")
    
    monkeypatch.setattr("psycopg2.connect", mock_connect)
    
    service = DatabaseService()
    assert service.pg_conn is None
    
    # Operations should fail gracefully
    result = service.store_repository_info(RepositoryInfo(
        name="test",
        url="test",
        local_path="test"
    ))
    assert not result

def test_handle_neo4j_connection_error(monkeypatch):
    """Test handling Neo4j connection errors"""
    def mock_driver(*args, **kwargs):
        raise Exception("Connection failed")
    
    monkeypatch.setattr(
        "neo4j.GraphDatabase.driver",
        mock_driver
    )
    
    service = DatabaseService()
    assert service.neo4j_conn is None
    
    # Operations should fail gracefully
    result = service.store_graph_data(
        nodes=[GraphNode(id="test", labels=["Test"], properties={})],
        relationships=[]
    )
    assert not result

def test_handle_redis_connection_error(monkeypatch):
    """Test handling Redis connection errors"""
    def mock_redis(*args, **kwargs):
        raise Exception("Connection failed")
    
    monkeypatch.setattr("redis.Redis", mock_redis)
    
    service = DatabaseService()
    assert service.redis_client is None
    
    # Operations should fail gracefully
    result = service.cache_analysis_result("key", "value")
    assert not result 