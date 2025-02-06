"""Database configuration module."""
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parents[4] / '.env'
load_dotenv(dotenv_path=env_path)

# PostgreSQL Configuration
POSTGRES_CONFIG: Dict[str, Any] = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "database": os.getenv("PGDATABASE", "postgres"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "")
}

# Neo4j Configuration
NEO4J_CONFIG: Dict[str, str] = {
    "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    "username": os.getenv("NEO4J_USERNAME", "neo4j"),
    "password": os.getenv("NEO4J_PASSWORD", "")
}

def get_postgres_config() -> Dict[str, Any]:
    """Get PostgreSQL configuration from environment variables.
    
    Returns:
        Dict containing PostgreSQL connection parameters
    """
    return POSTGRES_CONFIG

def get_neo4j_config() -> Dict[str, str]:
    """Get Neo4j configuration from environment variables.
    
    Returns:
        Dict containing Neo4j connection parameters
    """
    return NEO4J_CONFIG 