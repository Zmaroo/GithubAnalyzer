#!/usr/bin/env python
from datetime import datetime
import os
import click
import psycopg2
from neo4j import GraphDatabase
from dotenv import load_dotenv
import json
from typing import Dict, List, Optional, Any, Union
from ..config.config import PG_CONN_STRING, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
import shutil
from .models import (
    CodeRelationships,
    RepositoryInfo,
    GraphNode,
    GraphRelationship,
    RepositoryState,
    AnalysisSession,
    CodeSnippet,
    AnalysisCache,
    AnalysisStats,
    DatabaseConfig,
    GraphQuery
)
import redis
import pickle
import traceback
from .utils import setup_logger

logger = setup_logger(__name__)

load_dotenv()

class DatabaseManager:
    """Unified database management for all storage operations"""
    def __init__(self):
        self.pg_conn = self._init_postgres()
        self.neo4j_conn = self._init_neo4j()
        self.redis_client = self._init_redis()
        self.binary_redis = self._init_binary_redis()
        self.context_cache = {}  # Fallback in-memory cache

    def _init_postgres(self) -> Optional[psycopg2.extensions.connection]:
        """Initialize PostgreSQL connection"""
        try:
            return psycopg2.connect(PG_CONN_STRING)
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return None

    def _init_neo4j(self) -> Optional[GraphDatabase.driver]:
        """Initialize Neo4j connection"""
        try:
            return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            return None

    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis connection"""
        try:
            return redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}")
            return None

    def _init_binary_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis for binary data"""
        try:
            return redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=False
            )
        except Exception as e:
            logger.warning(f"Could not connect to binary Redis: {e}")
            return None

    def cache_analysis_result(self, key: str, data: Any, ttl: Optional[int] = 3600) -> bool:
        """
        Cache analysis results with optional TTL
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds (None for no expiry)
        Returns:
            bool: Success status
        """
        try:
            if self.redis_client:
                pickled_data = pickle.dumps(data)
                if ttl:
                    self.redis_client.set(key, pickled_data, ex=ttl)
                else:
                    self.redis_client.set(key, pickled_data)
            else:
                self.context_cache[key] = data
            return True
        except Exception as e:
            logger.error(f"Error caching analysis: {e}")
            logger.error(traceback.format_exc())
            return False

    def get_cached_analysis(self, key: str) -> Optional[Any]:
        """Retrieve cached analysis results"""
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                return pickle.loads(data) if data else None
            return self.context_cache.get(key)
        except Exception as e:
            logger.error(f"Error retrieving cache: {e}")
            logger.error(traceback.format_exc())
            return None

    def store_repository_info(self, repo_info: RepositoryInfo) -> bool:
        """Store repository information in PostgreSQL"""
        if not self.pg_conn:
            return False

        try:
            with self.pg_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO repository_info 
                    (url, last_analyzed, analysis_status, metadata)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE 
                    SET last_analyzed = EXCLUDED.last_analyzed,
                        analysis_status = EXCLUDED.analysis_status,
                        metadata = EXCLUDED.metadata
                """, (
                    repo_info.url,
                    repo_info.last_analyzed,
                    repo_info.analysis_status,
                    json.dumps(repo_info.metadata)
                ))
                self.pg_conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error storing repository info: {e}")
            logger.error(traceback.format_exc())
            return False

    def store_code_relationships(self, relationships: CodeRelationships) -> bool:
        """Store code relationships in Neo4j"""
        if not self.neo4j_conn:
            return False

        try:
            with self.neo4j_conn.session() as session:
                session.write_transaction(self._create_relationships, relationships)
                return True
        except Exception as e:
            logger.error(f"Error storing relationships: {e}")
            logger.error(traceback.format_exc())
            return False

    def cleanup(self):
        """Cleanup all database connections"""
        try:
            if self.pg_conn:
                self.pg_conn.close()
            if self.neo4j_conn:
                self.neo4j_conn.close()
            if self.redis_client:
                self.redis_client.close()
            if self.binary_redis:
                self.binary_redis.close()
            self.context_cache.clear()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _cache_key(self, repo_name: str, category: str) -> str:
        """Generate consistent cache keys"""
        return f"{repo_name}:{category}"

    def get_from_cache(self, repo_name: str, category: str) -> Optional[Any]:
        """Get data from cache (Redis or memory)"""
        if not self.redis_client:
            data = self.context_cache.get(f"{repo_name}:{category}")
            return self._deserialize_analysis(data) if data else None
            
        try:
            key = self._cache_key(repo_name, category)
            if category.endswith('_binary'):
                data = self.binary_redis.get(key)
                return pickle.loads(data) if data else None
            else:
                data = self.redis_client.get(key)
                if data:
                    return self._deserialize_analysis(json.loads(data))
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
            return None

    def store_in_cache(self, repo_name: str, category: str, data: Any, expire: int = 3600) -> bool:
        """Store data in cache with expiration"""
        if not self.redis_client:
            self.context_cache[f"{repo_name}:{category}"] = self._serialize_analysis(data)
            return True
            
        try:
            key = self._cache_key(repo_name, category)
            if category.endswith('_binary'):
                # Store binary data
                self.binary_redis.set(key, pickle.dumps(data), ex=expire)
            else:
                # Store JSON data
                serialized = self._serialize_analysis(data)
                self.redis_client.set(key, json.dumps(serialized), ex=expire)
            return True
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
            return False

    def clear_cache(self, repo_name: str) -> bool:
        """Clear all cached data for a repository"""
        try:
            if self.redis_client:
                pattern = f"{repo_name}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    
            # Clear binary cache
            if self.binary_redis:
                pattern = f"{repo_name}:*_binary"
                keys = self.binary_redis.keys(pattern)
                if keys:
                    self.binary_redis.delete(*keys)
                    
            # Clear memory cache
            keys_to_delete = [k for k in self.context_cache if k.startswith(f"{repo_name}:")]
            for k in keys_to_delete:
                del self.context_cache[k]
                
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def get_repository_info(self, repo_url: str = None) -> Optional[RepositoryInfo]:
        """Get repository information from PostgreSQL"""
        if not self.pg_conn:
            return None

        try:
            with self.pg_conn.cursor() as cur:
                if repo_url:
                    cur.execute("SELECT * FROM repository_info WHERE url = %s", (repo_url,))
                else:
                    cur.execute("SELECT * FROM repository_info ORDER BY last_analyzed DESC LIMIT 1")
                    
                row = cur.fetchone()
                if row:
                    return RepositoryInfo(
                        url=row[0],
                        last_analyzed=row[1],
                        analysis_status=row[2],
                        metadata=json.loads(row[3]) if row[3] else {}
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting repository info: {e}")
            return None

    def store_code_relationships(self, code_data: Dict[str, Any], repo_name: str) -> bool:
        """Store code relationships in Neo4j"""
        if not self.neo4j_conn:
            return False

        try:
            with self.neo4j_conn.session() as session:
                # Create repository node
                session.run("""
                    MERGE (r:Repository {name: $repo_name})
                """, repo_name=repo_name)

                # Store functions and their relationships
                for func in code_data.get('functions', []):
                    session.run("""
                        MATCH (r:Repository {name: $repo_name})
                        MERGE (f:Function {
                            name: $name,
                            file_path: $file_path,
                            line_number: $line_number
                        })
                        MERGE (f)-[:BELONGS_TO]->(r)
                    """, repo_name=repo_name, **func)

                # Store class hierarchies
                for cls in code_data.get('classes', []):
                    session.run("""
                        MATCH (r:Repository {name: $repo_name})
                        MERGE (c:Class {
                            name: $name,
                            file_path: $file_path
                        })
                        MERGE (c)-[:BELONGS_TO]->(r)
                    """, repo_name=repo_name, **cls)

                return True
        except Exception as e:
            logger.error(f"Error storing code relationships: {e}")
            return False

    def get_snippet_count(self, repo_name: Optional[str] = None) -> int:
        """Get count of stored code snippets"""
        if not self.pg_conn:
            return 0

        try:
            with self.pg_conn.cursor() as cur:
                if repo_name:
                    cur.execute("SELECT COUNT(*) FROM code_snippets WHERE repository = %s", (repo_name,))
                else:
                    cur.execute("SELECT COUNT(*) FROM code_snippets")
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting snippet count: {e}")
            return 0

    def _serialize_analysis(self, data: Any) -> Any:
        """Serialize analysis data for storage"""
        if isinstance(data, (dict, list)):
            return data
        elif hasattr(data, '__dict__'):
            return data.__dict__
        return str(data)

    def _deserialize_analysis(self, data: Any) -> Any:
        """Deserialize analysis data from storage"""
        return data  # Add custom deserialization if needed
