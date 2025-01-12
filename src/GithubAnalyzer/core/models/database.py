"""Database models and configuration"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    pg_conn_string: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    redis_host: str
    redis_port: int
    use_cache: bool = True

@dataclass
class DatabaseError:
    """Database operation error"""
    message: str
    code: Optional[str] = None
    details: Optional[dict] = None
    recoverable: bool = False
    
    def __str__(self) -> str:
        return f"Database error: {self.message} (code={self.code})" 