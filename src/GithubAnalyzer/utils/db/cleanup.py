"""Database cleanup utilities."""
from typing import Optional

from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

class DatabaseCleaner:
    """Utility class for cleaning up database resources."""
    
    def __init__(self):
        """Initialize the database cleaner."""
        from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
        from GithubAnalyzer.services.core.database.postgres_service import PostgresService
        self.pg_service = PostgresService()
        self.neo4j_service = Neo4jService()
        
    def cleanup_all(self) -> None:
        """Clean up all database resources."""
        self.cleanup_postgres()
        self.cleanup_neo4j()
        
    def cleanup_postgres(self) -> None:
        """Clean up PostgreSQL resources."""
        from GithubAnalyzer.services.core.database.postgres_service import PostgresService
        with PostgresService() as pg:
            pg.drop_tables()
            pg.create_tables()
            
    def cleanup_neo4j(self) -> None:
        """Clean up Neo4j resources."""
        from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
        with Neo4jService() as neo4j:
            # Delete all nodes and relationships
            neo4j._execute_query("MATCH (n) DETACH DELETE n")
            
            # Recreate constraints
            neo4j.setup_constraints()
            
    def cleanup_repository(self, repo_id: int) -> None:
        """Clean up all data for a specific repository.
        
        Args:
            repo_id: Repository identifier to clean up
        """
        from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
        from GithubAnalyzer.services.core.database.postgres_service import PostgresService
        
        with PostgresService() as pg:
            # Delete repository data from PostgreSQL
            pg._execute_query(
                "DELETE FROM code_snippets WHERE repo_id = %s",
                (repo_id,)
            )
            
        with Neo4jService() as neo4j:
            # Delete repository data from Neo4j
            neo4j._execute_query(
                "MATCH (n) WHERE n.repo_id = $repo_id DETACH DELETE n",
                {'repo_id': repo_id}
            ) 