from typing import Dict, Any, Optional, List
from ..models.database import DatabaseConfig, DatabaseError
from ..utils.decorators import singleton
from ..utils.logging import setup_logger
import atexit

logger = setup_logger(__name__)

@singleton
class DatabaseService(BaseService):
    """Unified database service for all storage operations"""
    
    def _initialize(self) -> None:
        """Initialize database connections and handlers"""
        try:
            self.config = self._load_config()
            self._init_connections()
            self._init_cleanup_handlers()
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise DatabaseError("Database initialization failed") from e

    def _init_connections(self) -> None:
        """Initialize all database connections"""
        self.connections = {
            'postgres': self._init_postgres(),
            'neo4j': self._init_neo4j(),
            'redis': self._init_redis()
        }
        
        # Validate critical connections
        if not self.connections['postgres']:
            raise DatabaseError("Failed to connect to PostgreSQL")
            
    def _init_cleanup_handlers(self) -> None:
        """Initialize cleanup handlers"""
        atexit.register(self.cleanup)
        
    def cleanup(self) -> None:
        """Clean up all database connections"""
        for name, conn in self.connections.items():
            try:
                if conn:
                    conn.close()
            except Exception as e:
                logger.error(f"Error closing {name} connection: {e}") 