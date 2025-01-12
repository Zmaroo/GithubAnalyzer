from typing import Dict, Any, Optional, List
import psycopg2
from neo4j import GraphDatabase
import redis
from ..models.database import (
    DatabaseConfig,
    RepositoryState,
    RepositoryInfo,
    GraphNode,
    GraphRelationship
)
from .base_service import BaseService
from ..utils.logging import setup_logger
import json
import pickle

logger = setup_logger(__name__)

class DatabaseService(BaseService):
    """Service for all database operations"""
    
    def _initialize(self) -> None:
        self.config = self._load_config()
        self.pg_conn = self._init_postgres()
        self.neo4j_conn = self._init_neo4j()
        self.redis_client = self._init_redis()
        
    def _load_config(self) -> DatabaseConfig:
        """Load database configuration"""
        from ...config.config import (
            PG_CONN_STRING, NEO4J_URI, 
            NEO4J_USER, NEO4J_PASSWORD
        )
        return DatabaseConfig(
            pg_conn_string=PG_CONN_STRING,
            neo4j_uri=NEO4J_URI,
            neo4j_user=NEO4J_USER,
            neo4j_password=NEO4J_PASSWORD
        )
        
    def _init_postgres(self) -> Optional[psycopg2.extensions.connection]:
        """Initialize PostgreSQL connection"""
        try:
            return psycopg2.connect(self.config.pg_conn_string)
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return None
            
    def _init_neo4j(self) -> Optional[GraphDatabase.driver]:
        """Initialize Neo4j connection"""
        try:
            return GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_user, self.config.neo4j_password)
            )
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            return None
            
    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis connection"""
        try:
            return redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None 

    def store_repository_info(self, repo_info: RepositoryInfo) -> bool:
        """Store repository information in PostgreSQL"""
        if not self.pg_conn:
            return False

        try:
            with self.pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO repository_info 
                    (name, url, local_path, last_analyzed, is_current, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE 
                    SET last_analyzed = EXCLUDED.last_analyzed,
                        is_current = EXCLUDED.is_current,
                        metadata = EXCLUDED.metadata
                """, (
                    repo_info.name,
                    repo_info.url,
                    repo_info.local_path,
                    repo_info.last_analyzed,
                    repo_info.is_current,
                    json.dumps(repo_info.metadata)
                ))
                self.pg_conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error storing repository info: {e}")
            return False

    def store_graph_data(self, nodes: List[GraphNode], relationships: List[GraphRelationship]) -> bool:
        """Store nodes and relationships in Neo4j"""
        if not self.neo4j_conn:
            return False

        try:
            with self.neo4j_conn.session() as session:
                # Store nodes
                for node in nodes:
                    session.run("""
                        MERGE (n:%s {id: $id})
                        SET n += $properties
                    """ % ':'.join(node.labels), {
                        'id': node.id,
                        'properties': node.properties
                    })

                # Store relationships
                for rel in relationships:
                    session.run("""
                        MATCH (a {id: $start_id}), (b {id: $end_id})
                        MERGE (a)-[r:%s]->(b)
                        SET r += $properties
                    """ % rel.type, {
                        'start_id': rel.start_node.id,
                        'end_id': rel.end_node.id,
                        'properties': rel.properties
                    })
                return True
        except Exception as e:
            logger.error(f"Error storing graph data: {e}")
            return False

    def cache_analysis_result(self, key: str, data: Any, ttl: Optional[int] = 3600) -> bool:
        """Cache analysis results with optional TTL"""
        try:
            if not self.redis_client:
                return False

            pickled_data = pickle.dumps(data)
            if ttl:
                self.redis_client.set(key, pickled_data, ex=ttl)
            else:
                self.redis_client.set(key, pickled_data)
            return True
        except Exception as e:
            logger.error(f"Error caching analysis: {e}")
            return False

    def get_cached_analysis(self, key: str) -> Optional[Any]:
        """Retrieve cached analysis results"""
        try:
            if not self.redis_client:
                return None

            data = self.redis_client.get(key)
            return pickle.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error retrieving cache: {e}")
            return None

    def cleanup(self):
        """Cleanup database connections"""
        try:
            if self.pg_conn:
                self.pg_conn.close()
            if self.neo4j_conn:
                self.neo4j_conn.close()
            if self.redis_client:
                self.redis_client.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 