"""Database configuration models."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..base import BaseModel


@dataclass
class RedisConfig(BaseModel):
    """Redis configuration."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    connection_pool: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Neo4jConfig(BaseModel):
    """Neo4j configuration."""

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "neo4j"
    database: str = "neo4j"
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50


@dataclass
class DatabaseConfig(BaseModel):
    """Database configuration."""

    redis: RedisConfig = field(default_factory=RedisConfig)
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    enable_caching: bool = True
    cache_ttl: int = 3600
    retry_attempts: int = 3
    timeout: int = 30
