from dotenv import load_dotenv
from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional, Tuple
import argparse
import os

from GithubAnalyzer.services.core.database.db_config import get_postgres_config, get_neo4j_config
"""Manual database testing and inspection utility.

This script provides direct access to database operations for testing and debugging purposes.
It can be run directly to test database connections and inspect database structures.
"""

import sys
from pathlib import Path
import psycopg2
import logging
# Add src directory to Python path
src_path = Path(__file__).resolve().parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseManualTester:
    """Manual database testing utility."""
    
    def __init__(self):
        """Initialize database connections."""
        # Load environment variables from .env file
        env_path = Path(__file__).parent.parent.parent.parent.parent / '.env'
        load_dotenv(env_path)
        self.pg_config = get_postgres_config()
        self.neo4j_config = get_neo4j_config()
        self.pg_conn = None
        self.neo4j_driver = None
        
    def test_postgres_connection(self) -> bool:
        """Test PostgreSQL connection and print connection info."""
        try:
            self.pg_conn = psycopg2.connect(
                dbname=self.pg_config["database"],
                user=self.pg_config["user"],
                password=self.pg_config["password"],
                host=self.pg_config["host"],
                port=self.pg_config["port"]
            )
            logger.info("Successfully connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {str(e)}")
            return False

    def create_postgres_database(self, dbname: str) -> bool:
        """Create a new PostgreSQL database."""
        try:
            # Connect to default database to create new one
            conn = psycopg2.connect(
                dbname="postgres",
                user=self.pg_config["user"],
                password=self.pg_config["password"],
                host=self.pg_config["host"],
                port=self.pg_config["port"]
            )
            conn.autocommit = True
            
            with conn.cursor() as cur:
                # Check if database exists
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
                if cur.fetchone():
                    logger.info(f"Database {dbname} already exists")
                    return True
                    
                # Create database
                cur.execute(f"CREATE DATABASE {dbname}")
                logger.info(f"Created database {dbname}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create database: {str(e)}")
            return False
            
    def init_postgres_schema(self) -> bool:
        """Initialize PostgreSQL schema and tables."""
        if not self.pg_conn:
            logger.error("No PostgreSQL connection")
            return False
            
        try:
            with self.pg_conn.cursor() as cur:
                # Enable vector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Create repositories table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS repositories (
                        id SERIAL PRIMARY KEY,
                        repo_url TEXT NOT NULL UNIQUE,
                        repo_name TEXT NOT NULL,
                        last_analyzed TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create code_snippets table with vector support
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS code_snippets (
                        id SERIAL PRIMARY KEY,
                        repo_id INTEGER REFERENCES repositories(id),
                        file_path TEXT NOT NULL,
                        content TEXT NOT NULL,
                        content_embedding vector(1536),
                        language TEXT,
                        start_line INTEGER,
                        end_line INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create functions table with docstring support
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS functions (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        start_line INTEGER,
                        end_line INTEGER,
                        docstring TEXT,
                        docstring_embedding vector(1536),
                        code_snippet_id INTEGER REFERENCES code_snippets(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create classes table with docstring support
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS classes (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        start_line INTEGER,
                        end_line INTEGER,
                        docstring TEXT,
                        docstring_embedding vector(1536),
                        code_snippet_id INTEGER REFERENCES code_snippets(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create comments table for non-docstring comments
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS comments (
                        id SERIAL PRIMARY KEY,
                        code_snippet_id INTEGER REFERENCES code_snippets(id),
                        content TEXT NOT NULL,
                        comment_type TEXT NOT NULL,
                        start_line INTEGER,
                        end_line INTEGER,
                        embedding vector(1536),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create indexes for faster lookups
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_functions_name ON functions(name);
                    CREATE INDEX IF NOT EXISTS idx_classes_name ON classes(name);
                    CREATE INDEX IF NOT EXISTS idx_code_snippets_repo ON code_snippets(repo_id);
                """)
                
                self.pg_conn.commit()
                logger.info("Successfully initialized PostgreSQL schema with vector support")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize schema: {str(e)}")
            return False
            
    def test_neo4j_connection(self) -> bool:
        """Test Neo4j connection and print connection info."""
        try:
            uri = self.neo4j_config["uri"]
            self.neo4j_driver = GraphDatabase.driver(
                uri,
                auth=(
                    self.neo4j_config["username"],
                    self.neo4j_config["password"]
                )
            )
            # Verify connection
            self.neo4j_driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j")
            return True
        except Exception as e:
            logger.error(f"Neo4j connection failed: {str(e)}")
            return False
            
    def init_neo4j_schema(self) -> bool:
        """Initialize Neo4j constraints and indexes."""
        if not self.neo4j_driver:
            logger.error("No Neo4j connection")
            return False
            
        try:
            with self.neo4j_driver.session() as session:
                # Create constraints
                session.run("""
                    CREATE CONSTRAINT repository_id IF NOT EXISTS
                    FOR (r:Repository) REQUIRE r.id IS UNIQUE
                """)
                
                session.run("""
                    CREATE CONSTRAINT function_id IF NOT EXISTS
                    FOR (f:Function) REQUIRE f.id IS UNIQUE
                """)
                
                session.run("""
                    CREATE CONSTRAINT class_id IF NOT EXISTS
                    FOR (c:Class) REQUIRE c.id IS UNIQUE
                """)
                
                session.run("""
                    CREATE CONSTRAINT module_id IF NOT EXISTS
                    FOR (m:Module) REQUIRE m.id IS UNIQUE
                """)
                
                # Create indexes
                session.run("""
                    CREATE INDEX function_name IF NOT EXISTS
                    FOR (f:Function) ON (f.name)
                """)
                
                session.run("""
                    CREATE INDEX class_name IF NOT EXISTS
                    FOR (c:Class) ON (c.name)
                """)
                
                logger.info("Successfully initialized Neo4j schema")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j schema: {str(e)}")
            return False
            
    def get_postgres_info(self) -> Dict[str, Any]:
        """Get PostgreSQL database information."""
        if not self.pg_conn:
            logger.error("No PostgreSQL connection")
            return {}
            
        info = {}
        try:
            with self.pg_conn.cursor() as cur:
                # Get database name
                cur.execute("SELECT current_database();")
                info["database"] = cur.fetchone()[0]
                
                # Get schemas
                cur.execute("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog');
                """)
                info["schemas"] = [row[0] for row in cur.fetchall()]
                
                # Get tables for each schema
                info["tables"] = {}
                for schema in info["schemas"]:
                    cur.execute(f"""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s;
                    """, (schema,))
                    info["tables"][schema] = [row[0] for row in cur.fetchall()]
                    
                # Get row counts for each table
                info["row_counts"] = {}
                for schema in info["schemas"]:
                    for table in info["tables"][schema]:
                        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table};")
                        info["row_counts"][f"{schema}.{table}"] = cur.fetchone()[0]
                        
            return info
        except Exception as e:
            logger.error(f"Error getting PostgreSQL info: {str(e)}")
            return {}
            
    def get_neo4j_info(self) -> Dict[str, Any]:
        """Get Neo4j database information."""
        if not self.neo4j_driver:
            logger.error("No Neo4j connection")
            return {}
            
        info = {}
        try:
            with self.neo4j_driver.session() as session:
                # Get node labels
                result = session.run("CALL db.labels()")
                info["labels"] = [record["label"] for record in result]
                
                # Get relationship types
                result = session.run("CALL db.relationshipTypes()")
                info["relationship_types"] = [record["relationshipType"] for record in result]
                
                # Get node counts by label
                info["node_counts"] = {}
                for label in info["labels"]:
                    result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                    info["node_counts"][label] = result.single()["count"]
                    
                # Get relationship counts by type
                info["relationship_counts"] = {}
                for rel_type in info["relationship_types"]:
                    result = session.run(
                        f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                    )
                    info["relationship_counts"][rel_type] = result.single()["count"]
                    
            return info
        except Exception as e:
            logger.error(f"Error getting Neo4j info: {str(e)}")
            return {}
            
    def close(self):
        """Close database connections."""
        if self.pg_conn:
            self.pg_conn.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()

def main():
    """Run manual database tests."""
    parser = argparse.ArgumentParser(description="Database Manual Testing Utility")
    parser.add_argument('--create-db', help='Create a new PostgreSQL database')
    parser.add_argument('--init-schema', action='store_true', help='Initialize database schemas')
    args = parser.parse_args()
    
    tester = DatabaseManualTester()
    
    # Create database if requested
    if args.create_db:
        if tester.create_postgres_database(args.create_db):
            logger.info(f"Successfully created database: {args.create_db}")
        else:
            sys.exit(1)
    
    # Test PostgreSQL
    logger.info("Testing PostgreSQL connection...")
    if tester.test_postgres_connection():
        # Initialize schema if requested
        if args.init_schema:
            tester.init_postgres_schema()
        
        # Get and display info
        pg_info = tester.get_postgres_info()
        logger.info("PostgreSQL Information:")
        logger.info(f"Database: {pg_info.get('database')}")
        logger.info(f"Schemas: {pg_info.get('schemas')}")
        logger.info("Tables:")
        for schema, tables in pg_info.get('tables', {}).items():
            logger.info(f"  {schema}:")
            for table in tables:
                count = pg_info['row_counts'].get(f"{schema}.{table}", 0)
                logger.info(f"    - {table} ({count} rows)")
    
    # Test Neo4j
    logger.info("\nTesting Neo4j connection...")
    if tester.test_neo4j_connection():
        # Initialize schema if requested
        if args.init_schema:
            tester.init_neo4j_schema()
        
        # Get and display info
        neo4j_info = tester.get_neo4j_info()
        logger.info("Neo4j Information:")
        logger.info(f"Node Labels: {neo4j_info.get('labels')}")
        logger.info("Node Counts:")
        for label, count in neo4j_info.get('node_counts', {}).items():
            logger.info(f"  - {label}: {count}")
        logger.info("\nRelationship Types:")
        for rel_type, count in neo4j_info.get('relationship_counts', {}).items():
            logger.info(f"  - {rel_type}: {count}")
    
    tester.close()

if __name__ == "__main__":
    main() 