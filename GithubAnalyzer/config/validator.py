"""Configuration validation"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import os
from urllib.parse import urlparse

@dataclass
class ConfigError:
    """Configuration error"""
    path: str
    message: str
    severity: str = "error"

class ConfigValidator:
    """Configuration validator"""
    
    @classmethod
    def validate(cls, config_path: Optional[str] = None) -> List[ConfigError]:
        """Validate configuration"""
        errors = []
        
        # Required environment variables
        required_vars = {
            'PG_CONN_STRING': "PostgreSQL connection string",
            'NEO4J_URI': "Neo4j URI",
            'NEO4J_USER': "Neo4j username",
            'NEO4J_PASSWORD': "Neo4j password"
        }
        
        for var, description in required_vars.items():
            if not os.getenv(var):
                errors.append(ConfigError(
                    path=var,
                    message=f"{description} not configured"
                ))
                
        # Validate PostgreSQL connection string
        pg_conn = os.getenv('PG_CONN_STRING', '')
        try:
            parsed = urlparse(pg_conn)
            if not all([parsed.hostname, parsed.username, parsed.password]):
                errors.append(ConfigError(
                    path="PG_CONN_STRING",
                    message="Invalid PostgreSQL connection string format"
                ))
        except Exception:
            errors.append(ConfigError(
                path="PG_CONN_STRING",
                message="Could not parse PostgreSQL connection string"
            ))
            
        # Validate Neo4j URI
        neo4j_uri = os.getenv('NEO4J_URI', '')
        if not neo4j_uri.startswith(('bolt://', 'neo4j://')):
            errors.append(ConfigError(
                path="NEO4J_URI",
                message="Neo4j URI must start with bolt:// or neo4j://"
            ))
            
        return errors 