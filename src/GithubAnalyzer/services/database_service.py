"""Database service for handling database operations"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import psycopg2
from neo4j import GraphDatabase
import redis
import json
from .configurable import ConfigurableService, DatabaseConfig
from .errors import DatabaseError
from ..models.repository import RepositoryState, RepositoryInfo
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

@dataclass
class ConnectionMetrics:
    """Database connection metrics"""
    active_connections: int = 0
    pool_size: int = 0
    wait_time: float = 0.0
    timeout_count: int = 0

class DatabaseService(ConfigurableService):
    """Service for database operations"""
    
    def __init__(self, registry=None, config: Optional[DatabaseConfig] = None):
        self.pg_conn = None
        self.neo4j_conn = None
        self.redis_conn = None
        self.cache = {}
        self.metrics = ConnectionMetrics()
        super().__init__(registry, config or DatabaseConfig())
        
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize database connections"""
        try:
            if config:
                self._update_config(config)
                
            # Validate SSL requirements from cursorrules
            if self.service_config.enable_ssl:
                self._setup_ssl()
                
            # Initialize connections using config
            db_config = self.service_config
            self._init_postgres(db_config)
            self._init_neo4j(db_config)
            self._init_redis(db_config)
            
            # Setup connection pooling as required by cursorrules
            if db_config.connection_pooling:
                self._setup_connection_pool(
                    max_connections=db_config.max_connections,
                    timeout=db_config.connection_timeout
                )
            
        except Exception as e:
            raise DatabaseError(message="Failed to initialize database connections", 
                              details={"error": str(e)})

    def _setup_ssl(self) -> None:
        """Setup SSL configuration"""
        try:
            # Implementation of SSL setup
            logger.info("Setting up SSL for database connections")
            # Add SSL setup code here
        except Exception as e:
            raise DatabaseError(message="Failed to setup SSL", 
                              details={"error": str(e)})

    def _setup_connection_pool(self, max_connections: int, timeout: int) -> None:
        """Setup connection pooling"""
        try:
            # Implementation of connection pooling
            logger.info(f"Setting up connection pool: max={max_connections}, timeout={timeout}")
            # Add connection pooling setup code here
        except Exception as e:
            raise DatabaseError(message="Failed to setup connection pool", 
                              details={"error": str(e)})

    def _validate_requirements(self) -> bool:
        """Validate service requirements from cursorrules"""
        if not super()._validate_requirements():
            return False
            
        config = self.service_config
        
        # Check SSL requirement
        if config.require_ssl and not config.enable_ssl:
            logger.error("SSL is required but not enabled")
            return False
            
        # Check connection pooling requirement
        if config.connection_pooling and config.max_connections <= 0:
            logger.error("Invalid connection pool configuration")
            return False
            
        return True

    def _cleanup(self) -> None:
        """Cleanup database connections"""
        try:
            if self.pg_conn:
                self.pg_conn.close()
            if self.neo4j_conn:
                self.neo4j_conn.close()
            if self.redis_conn:
                self.redis_conn.close()
            self.cache.clear()
        except Exception as e:
            logger.error(f"Failed to cleanup database connections: {e}")

    def get_metrics(self) -> ConnectionMetrics:
        """Get database connection metrics"""
        return self.metrics

    def _init_postgres(self, config: DatabaseConfig) -> None:
        """Initialize PostgreSQL connection"""
        try:
            # Mock for now
            self.pg_conn = psycopg2.connect(
                host=config.host,
                port=config.port,
                database=config.database,
                user=config.username,
                password=config.password
            )
        except Exception as e:
            raise DatabaseError(message="Failed to initialize PostgreSQL", details={"error": str(e)})

    def _init_neo4j(self, config: DatabaseConfig) -> None:
        """Initialize Neo4j connection"""
        try:
            self.neo4j_conn = GraphDatabase.driver(
                config.neo4j_uri,
                auth=(config.neo4j_user, config.neo4j_password)
            )
        except Exception as e:
            raise DatabaseError(message="Failed to initialize Neo4j", details={"error": str(e)})

    def _init_redis(self, config: DatabaseConfig) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_conn = redis.Redis(
                host=config.host,
                port=config.redis_port,
                db=0,
                decode_responses=True
            )
        except Exception as e:
            raise DatabaseError(message="Failed to initialize Redis", details={"error": str(e)})

    def store_repository_state(self, state: RepositoryState) -> bool:
        """Store repository state"""
        if not self.initialized:
            return False
            
        try:
            # Store in PostgreSQL
            with self.pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO repository_states 
                    (url, status, progress, current_operation, last_update)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE 
                    SET status = EXCLUDED.status,
                        progress = EXCLUDED.progress,
                        current_operation = EXCLUDED.current_operation,
                        last_update = EXCLUDED.last_update
                """, (
                    state.url,
                    state.status,
                    state.progress,
                    state.current_operation,
                    state.last_update
                ))
                self.pg_conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store repository state: {e}")
            return False

    def cache_analysis_result(self, key: str, data: Any, ttl: int = 3600) -> bool:
        """Cache analysis results"""
        if not self.initialized or not self.service_config.cache_enabled:
            return False
            
        try:
            if self.redis_conn:
                self.redis_conn.set(key, str(data), ex=ttl)
            else:
                self.cache[key] = data
            return True
        except Exception as e:
            logger.error(f"Failed to cache analysis result: {e}")
            return False

    def store_graph_data(self, nodes: list, relationships: list) -> bool:
        """Store graph data in Neo4j"""
        if not self.initialized or not self.neo4j_conn:
            return False
            
        try:
            with self.neo4j_conn.session() as session:
                # Create nodes
                for node in nodes:
                    session.run(
                        "CREATE (n:CodeNode $props)",
                        props=node
                    )
                    
                # Create relationships
                for rel in relationships:
                    session.run("""
                        MATCH (a:CodeNode {id: $from})
                        MATCH (b:CodeNode {id: $to})
                        CREATE (a)-[r:RELATES {type: $type}]->(b)
                    """, rel)
                    
            return True
        except Exception as e:
            logger.error(f"Failed to store graph data: {e}")
            return False 

    def store_repository_info(self, repo_info: RepositoryInfo) -> bool:
        """Store repository information"""
        if not self.initialized:
            return False
        
        try:
            with self.pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO repository_info 
                    (name, url, local_path, metadata, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE 
                    SET metadata = EXCLUDED.metadata,
                        updated_at = EXCLUDED.updated_at
                """, (
                    repo_info.name,
                    repo_info.url,
                    repo_info.local_path,
                    json.dumps(repo_info.metadata),
                    repo_info.created_at,
                    repo_info.updated_at
                ))
                self.pg_conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store repository info: {e}")
            return False 