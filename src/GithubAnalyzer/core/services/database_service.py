"""Database service for handling database operations"""
import psycopg2
import redis
from neo4j import GraphDatabase
from typing import Optional, Dict, Any, List
from ..utils.decorators import singleton
from ..models.database import (
    DatabaseConfig, 
    DatabaseError,
    RepositoryState,
    RepositoryInfo,
    DatabaseConnection
)
from .base import BaseService
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

@singleton
class DatabaseService(BaseService):
    """Service for database operations"""
    
    def __init__(self, registry=None):
        """Initialize database service"""
        super().__init__(registry)
        self.config: Optional[DatabaseConfig] = None
        self.connection = DatabaseConnection()
        
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize database connections"""
        if config and isinstance(config, dict):
            self.config = DatabaseConfig(**config.get("database", {}))
        else:
            # Use default config for testing
            self.config = DatabaseConfig(
                pg_conn_string="postgresql://postgres:postgres@localhost:5432/code_analysis",
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j",
                neo4j_password="password",
                redis_host="localhost",
                redis_port=6379,
                use_cache=True
            )
            
        self._init_postgres()
        self._init_neo4j()
        self._init_redis()
        
    def _init_postgres(self) -> None:
        """Initialize PostgreSQL connection"""
        try:
            self.connection.pg_conn = psycopg2.connect(self.config.pg_conn_string)
            self.connection.is_connected = True
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            self.connection.last_error = str(e)
            
    def _init_neo4j(self) -> None:
        """Initialize Neo4j connection"""
        try:
            driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_user, self.config.neo4j_password)
            )
            self.connection.neo4j_conn = driver
            self.connection.is_connected = True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.connection.last_error = str(e)
            
    def _init_redis(self) -> None:
        """Initialize Redis connection"""
        try:
            self.connection.redis_conn = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                decode_responses=True
            )
            self.connection.is_connected = True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connection.last_error = str(e)
            
    def shutdown(self) -> bool:
        """Close database connections"""
        try:
            if self.connection.pg_conn:
                self.connection.pg_conn.close()
            if self.connection.neo4j_conn:
                self.connection.neo4j_conn.close()
            if self.connection.redis_conn:
                self.connection.redis_conn.close()
            self.initialized = False
            return True
        except Exception as e:
            logger.error(f"Failed to shutdown database: {e}")
            return False
            
    def cleanup(self) -> None:
        """Cleanup database resources"""
        self.shutdown()

    def store_repository_info(self, repo_info: RepositoryInfo) -> bool:
        """Store repository information"""
        if not self.connection.pg_conn:
            return False
            
        try:
            with self.connection.pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO repository_info 
                    (name, url, local_path, metadata, last_analyzed, frameworks, languages, is_current, analysis_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE 
                    SET last_analyzed = EXCLUDED.last_analyzed,
                        metadata = EXCLUDED.metadata,
                        frameworks = EXCLUDED.frameworks,
                        languages = EXCLUDED.languages,
                        is_current = EXCLUDED.is_current,
                        analysis_status = EXCLUDED.analysis_status
                """, (
                    repo_info.name,
                    repo_info.url,
                    repo_info.local_path,
                    repo_info.metadata,
                    repo_info.last_analyzed,
                    repo_info.frameworks,
                    repo_info.languages,
                    repo_info.is_current,
                    repo_info.analysis_status
                ))
                self.connection.pg_conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error storing repository info: {e}")
            return False

    def store_repository_state(self, state: RepositoryState) -> bool:
        """Store repository analysis state"""
        if not self.connection.pg_conn:
            return False
            
        try:
            with self.connection.pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO repository_state 
                    (url, status, progress, errors, last_update, metadata, current_operation, operation_started, operation_progress)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE 
                    SET status = EXCLUDED.status,
                        progress = EXCLUDED.progress,
                        errors = EXCLUDED.errors,
                        last_update = EXCLUDED.last_update,
                        metadata = EXCLUDED.metadata,
                        current_operation = EXCLUDED.current_operation,
                        operation_started = EXCLUDED.operation_started,
                        operation_progress = EXCLUDED.operation_progress
                """, (
                    state.url,
                    state.status,
                    state.progress,
                    state.errors,
                    state.last_update,
                    state.metadata,
                    state.current_operation,
                    state.operation_started,
                    state.operation_progress
                ))
                self.connection.pg_conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error storing repository state: {e}")
            return False

    def store_graph_data(self, nodes: List[Any], relationships: List[Any]) -> bool:
        """Store graph data in Neo4j"""
        if not self.connection.neo4j_conn:
            return False
            
        try:
            session = self.connection.neo4j_conn.session()
            for node in nodes:
                session.run(
                    "CREATE (n:$labels {id: $id, properties: $properties})",
                    labels=node.labels,
                    id=node.id,
                    properties=node.properties
                )
            for rel in relationships:
                session.run(
                    "MATCH (a {id: $start_id}), (b {id: $end_id}) "
                    "CREATE (a)-[r:$type {properties: $properties}]->(b)",
                    start_id=rel.start_node,
                    end_id=rel.end_node,
                    type=rel.type,
                    properties=rel.properties
                )
            return True
        except Exception as e:
            logger.error(f"Error storing graph data: {e}")
            return False

    def cache_analysis_result(self, key: str, data: Any, ttl: Optional[int] = 3600) -> bool:
        """Cache analysis results"""
        if not self.connection.redis_conn:
            return False
            
        try:
            if ttl:
                self.connection.redis_conn.setex(key, ttl, str(data))
            else:
                self.connection.redis_conn.set(key, str(data))
            return True
        except Exception as e:
            logger.error(f"Error caching analysis: {e}")
            return False

    def get_cached_analysis(self, key: str) -> Optional[Any]:
        """Get cached analysis results"""
        if not self.connection.redis_conn:
            return None
            
        try:
            return self.connection.redis_conn.get(key)
        except Exception as e:
            logger.error(f"Error retrieving cache: {e}")
            return None

    @property
    def pg_conn(self):
        """Get PostgreSQL connection"""
        return self.connection.pg_conn

    @property
    def neo4j_conn(self):
        """Get Neo4j connection"""
        return self.connection.neo4j_conn

    @property
    def redis_client(self):
        """Get Redis connection"""
        return self.connection.redis_conn 