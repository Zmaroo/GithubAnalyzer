from typing import Optional, Tuple, List
from neo4j.exceptions import ServiceUnavailable

from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
import psycopg2
from GithubAnalyzer.services.core.database.postgres_service import PostgresService
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

class DatabaseCleaner:
    """Utility class for cleaning up databases."""
    
    def __init__(self):
        self.pg_service = PostgresService()
        self.neo4j_service = Neo4jService()
    
    def test_connections(self) -> Tuple[bool, List[str]]:
        """Test connections to both databases.
        
        Returns:
            Tuple of (success, list of error messages)
        """
        errors = []
        success = True
        
        # Test PostgreSQL
        try:
            with self.pg_service as pg:
                with pg._conn.cursor() as cur:
                    cur.execute("SELECT 1")
        except psycopg2.Error as e:
            success = False
            errors.append(f"PostgreSQL connection failed: {str(e)}")
        
        # Test Neo4j
        try:
            with self.neo4j_service as neo4j:
                with neo4j._driver.session() as session:
                    session.run("RETURN 1")
        except ServiceUnavailable as e:
            success = False
            errors.append(f"Neo4j connection failed: {str(e)}")
        except Exception as e:
            success = False
            errors.append(f"Neo4j error: {str(e)}")
        
        return success, errors
    
    def cleanup_postgres(self) -> None:
        """Clean up all data in PostgreSQL."""
        try:
            with self.pg_service as pg:
                with pg._conn.cursor() as cur:
                    cur.execute("""
                        TRUNCATE TABLE code_snippets;
                    """)
                    pg._conn.commit()
            logger.info("Successfully cleaned PostgreSQL database")
        except psycopg2.Error as e:
            logger.error(f"Failed to clean PostgreSQL database: {str(e)}")
            raise
    
    def cleanup_neo4j(self) -> None:
        """Clean up all data in Neo4j."""
        try:
            with self.neo4j_service as neo4j:
                with neo4j._driver.session() as session:
                    session.run("""
                        MATCH (n)
                        DETACH DELETE n
                    """)
            logger.info("Successfully cleaned Neo4j database")
        except Exception as e:
            logger.error(f"Failed to clean Neo4j database: {str(e)}")
            raise
    
    def cleanup_all(self) -> None:
        """Clean up all databases."""
        # First test connections
        success, errors = self.test_connections()
        if not success:
            error_msg = "\n".join(errors)
            logger.error(f"Database connection test failed:\n{error_msg}")
            raise ConnectionError(f"Failed to connect to databases:\n{error_msg}")
        
        # If connections are good, proceed with cleanup
        self.cleanup_postgres()
        self.cleanup_neo4j()
        logger.info("Successfully cleaned all databases")

def cleanup_databases() -> None:
    """Convenience function to clean all databases."""
    try:
        cleaner = DatabaseCleaner()
        cleaner.cleanup_all()
        print("Successfully cleaned all databases.")
    except Exception as e:
        print(f"Error cleaning databases: {str(e)}")
        logger.exception("Database cleanup failed") 