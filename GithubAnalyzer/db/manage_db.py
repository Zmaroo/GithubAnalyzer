#!/usr/bin/env python
import os
import click
import logging
import psycopg2
from neo4j import GraphDatabase
from dotenv import load_dotenv
from ..config.config import PG_CONN_STRING, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.neo4j_driver = None
        self.connect()

    def connect(self):
        """Connect to both PostgreSQL and Neo4j databases"""
        try:
            self.conn = psycopg2.connect(PG_CONN_STRING)
            logger.info("Connected to PostgreSQL")
            logger.info(f"Connecting to Neo4j at {os.getenv('NEO4J_URI')}")
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    os.getenv('NEO4J_URI'),
                    auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
                )
                # Verify connection
                with self.neo4j_driver.session() as session:
                    result = session.run("RETURN 1")
                    result.single()
                logger.info("Successfully connected to Neo4j")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Error connecting to databases: {e}")
            self.cleanup()
            raise

    def cleanup(self):
        """Close all database connections"""
        if self.conn:
            self.conn.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()

    def clear_all_data(self):
        """Clear all data from both databases"""
        try:
            # Clear PostgreSQL
            with self.conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE code_snippets CASCADE")
                cur.execute("TRUNCATE TABLE repositories CASCADE")
                self.conn.commit()
                logger.info("PostgreSQL data cleared")

            # Clear Neo4j
            with self.neo4j_driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("Neo4j data cleared")

        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            raise

    def verify_connections(self):
        """Verify database connections are working"""
        try:
            # Check PostgreSQL
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
                logger.info("PostgreSQL connection verified")

            # Check Neo4j
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
                logger.info("Neo4j connection verified")

        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            raise

    def repair_database_state(self):
        """Repair database inconsistencies"""
        try:
            logger.info("Starting database repair...")
            
            # Fix PostgreSQL
            with self.conn.cursor() as cur:
                # Remove orphaned entries
                cur.execute("""
                    DELETE FROM active_sessions a
                    WHERE NOT EXISTS (
                        SELECT 1 FROM repository_state rs
                        WHERE rs.id = a.repository_id
                    )
                """)
                logger.info("Cleaned orphaned PostgreSQL entries")

                # Ensure repository_state table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS repository_state (
                        id SERIAL PRIMARY KEY,
                        repository_name TEXT UNIQUE NOT NULL,
                        repository_url TEXT NOT NULL,
                        local_path TEXT,
                        last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_current BOOLEAN DEFAULT false
                    )
                """)

                # Ensure active_sessions table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS active_sessions (
                        session_id TEXT,
                        repository_id INTEGER REFERENCES repository_state(id),
                        activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        context JSONB,
                        PRIMARY KEY (session_id, repository_id)
                    )
                """)
                
                self.conn.commit()
                logger.info("PostgreSQL schema verified")

            # Fix Neo4j
            with self.neo4j_driver.session() as session:
                # Clean orphaned nodes
                session.run("""
                    MATCH (n:CodeNode)
                    WHERE NOT (n)-[:DEFINED_IN]->(:File)
                    DELETE n
                """)
                logger.info("Cleaned orphaned Neo4j nodes")

                # Ensure constraints exist
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE
                """)
                session.run("""
                    CREATE CONSTRAINT IF NOT EXISTS FOR (fn:CodeNode) REQUIRE fn.unique_id IS UNIQUE
                """)
                logger.info("Neo4j constraints verified")

            return True
        except Exception as e:
            logger.error(f"Error during repair: {e}")
            return False

    def show_database_status(self):
        """Show detailed database status"""
        try:
            # PostgreSQL status
            with self.conn.cursor() as cur:
                # Get table names first
                cur.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                tables = [row[0] for row in cur.fetchall()]
                
                logger.info("\nPostgreSQL Tables:")
                for table in tables:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    logger.info(f"- {table}: {count} rows")

            # Neo4j status (without requiring APOC)
            with self.neo4j_driver.session() as session:
                # Get node counts by label
                node_counts = session.run("""
                    MATCH (n)
                    WITH labels(n) as labels, count(n) as count
                    RETURN labels, count
                """)
                
                # Get relationship counts by type
                rel_counts = session.run("""
                    MATCH ()-[r]->()
                    WITH type(r) as rel_type, count(r) as count
                    RETURN rel_type, count
                """)
                
                logger.info("\nNeo4j Database:")
                logger.info("Node Types:")
                for record in node_counts:
                    logger.info(f"- {record['labels']}: {record['count']}")
                
                logger.info("Relationship Types:")
                for record in rel_counts:
                    logger.info(f"- {record['rel_type']}: {record['count']}")

        except Exception as e:
            logger.error(f"Error getting status: {e}")
            raise

    def init_schema(self):
        """Initialize database schema"""
        try:
            logger.info("Initializing database schema...")
            
            # PostgreSQL schema
            with self.conn.cursor() as cur:
                # Repository state table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS repository_state (
                        id SERIAL PRIMARY KEY,
                        repository_name TEXT UNIQUE NOT NULL,
                        repository_url TEXT NOT NULL,
                        local_path TEXT,
                        last_analyzed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        is_current BOOLEAN DEFAULT false
                    )
                """)

                # Active sessions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS active_sessions (
                        session_id TEXT,
                        repository_id INTEGER REFERENCES repository_state(id),
                        activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        context JSONB,
                        PRIMARY KEY (session_id, repository_id)
                    )
                """)
                
                self.conn.commit()
                logger.info("PostgreSQL schema initialized")

            # Neo4j schema
            with self.neo4j_driver.session() as session:
                session.execute_write(lambda tx: tx.run("""
                    CREATE CONSTRAINT file_path_unique IF NOT EXISTS 
                    FOR (f:File) REQUIRE f.path IS UNIQUE
                """))
                session.execute_write(lambda tx: tx.run("""
                    CREATE CONSTRAINT code_node_id_unique IF NOT EXISTS 
                    FOR (fn:CodeNode) REQUIRE fn.unique_id IS UNIQUE
                """))
                logger.info("Neo4j schema initialized")

            return True
        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
            self.conn.rollback()
            return False

    def validate_schema(self):
        """Validate database schema and structure"""
        try:
            logger.info("Validating database schema...")
            issues = []
            
            # PostgreSQL validation
            with self.conn.cursor() as cur:
                # Check tables exist
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = {row[0] for row in cur.fetchall()}
                required_tables = {'repository_state', 'active_sessions'}
                
                for table in required_tables - tables:
                    issues.append(f"Missing PostgreSQL table: {table}")
                
                # Check columns
                if 'repository_state' in tables:
                    cur.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'repository_state'
                    """)
                    columns = {row[0]: row[1] for row in cur.fetchall()}
                    
                    required_columns = {
                        'id': 'integer',
                        'repository_name': 'text',
                        'repository_url': 'text',
                        'local_path': 'text',
                        'last_analyzed': 'timestamp with time zone',
                        'is_current': 'boolean'
                    }
                    
                    for col, type_ in required_columns.items():
                        if col not in columns:
                            issues.append(f"Missing column: repository_state.{col}")
                        elif columns[col] != type_:
                            issues.append(f"Wrong type for repository_state.{col}: expected {type_}, got {columns[col]}")
            
            # Neo4j validation
            with self.neo4j_driver.session() as session:
                # Check constraints
                constraints = session.run("SHOW CONSTRAINTS").data()
                constraint_names = {c['name'] for c in constraints}
                
                required_constraints = {
                    'file_path_unique',
                    'code_node_id_unique'
                }
                
                for constraint in required_constraints - constraint_names:
                    issues.append(f"Missing Neo4j constraint: {constraint}")
            
            if issues:
                logger.warning("Schema validation issues found:")
                for issue in issues:
                    logger.warning(f"- {issue}")
                return False
            
            logger.info("Schema validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating schema: {e}")
            return False

    def repair_schema(self):
        """Fix schema issues"""
        try:
            logger.info("Repairing schema issues...")
            
            # Fix PostgreSQL timestamp type
            with self.conn.cursor() as cur:
                cur.execute("""
                    ALTER TABLE repository_state 
                    ALTER COLUMN last_analyzed TYPE TIMESTAMP WITH TIME ZONE 
                    USING last_analyzed AT TIME ZONE 'UTC'
                """)
                self.conn.commit()
                logger.info("Fixed PostgreSQL timestamp type")

            # Drop and recreate Neo4j constraints with correct names
            with self.neo4j_driver.session() as session:
                # Drop existing constraints
                session.run("DROP CONSTRAINT constraint_c4752a78 IF EXISTS")
                session.run("DROP CONSTRAINT constraint_f9e34484 IF EXISTS")
                
                # Create with correct names
                session.run("""
                    CREATE CONSTRAINT file_path_unique IF NOT EXISTS 
                    FOR (f:File) REQUIRE f.path IS UNIQUE
                """)
                session.run("""
                    CREATE CONSTRAINT code_node_id_unique IF NOT EXISTS 
                    FOR (fn:CodeNode) REQUIRE fn.unique_id IS UNIQUE
                """)
                logger.info("Fixed Neo4j constraints")

            return True
        except Exception as e:
            logger.error(f"Error repairing schema: {e}")
            self.conn.rollback()
            return False

    def run_graph_analysis(self):
        """Run graph analysis algorithms"""
        try:
            with self.neo4j_driver.session() as session:
                # Create GDS graph projection
                session.run("""
                    CALL gds.graph.project(
                        'code_graph',
                        ['CodeNode', 'File'],
                        {
                            DEFINED_IN: {orientation: 'UNDIRECTED'},
                            CALLS: {orientation: 'NATURAL'}
                        }
                    )
                """)

                # Run PageRank to find important components
                session.run("""
                    CALL gds.pageRank.write(
                        'code_graph',
                        {
                            writeProperty: 'pagerank',
                            maxIterations: 20
                        }
                    )
                """)

                # Find communities using Louvain
                session.run("""
                    CALL gds.louvain.write(
                        'code_graph',
                        {
                            writeProperty: 'community'
                        }
                    )
                """)

                # Generate node embeddings
                session.run("""
                    CALL gds.fastRP.write(
                        'code_graph',
                        {
                            writeProperty: 'embedding',
                            embeddingDimension: 128
                        }
                    )
                """)

                logger.info("Graph analysis complete")
                return True

        except Exception as e:
            logger.error(f"Error running graph analysis: {e}")
            return False

@click.group()
def cli():
    """Database management tool for GithubAnalyzer"""
    pass

@cli.command()
def status():
    """Show current database status"""
    db = DatabaseManager()
    try:
        db.show_database_status()
    finally:
        db.cleanup()

@cli.command()
@click.option('--force', is_flag=True, help='Force clear without confirmation')
def clear(force):
    """Clear all data from databases"""
    if not force and not click.confirm('Are you sure you want to clear all data?'):
        return
    db = DatabaseManager()
    try:
        db.clear_all_data()
    finally:
        db.cleanup()

@cli.command()
def verify():
    """Verify database connections"""
    db = DatabaseManager()
    try:
        db.verify_connections()
    finally:
        db.cleanup()

@cli.command()
def repair():
    """Repair schema issues"""
    db = DatabaseManager()
    try:
        if db.repair_schema():
            logger.info("Schema repair complete")
        else:
            logger.error("Schema repair failed")
    finally:
        db.cleanup()

@cli.command()
def init():
    """Initialize database schema"""
    db = DatabaseManager()
    try:
        if db.init_schema():
            logger.info("Schema initialization complete")
        else:
            logger.error("Schema initialization failed")
    finally:
        db.cleanup()

@cli.command()
def validate():
    """Validate database schema"""
    db = DatabaseManager()
    try:
        if db.validate_schema():
            logger.info("Schema validation passed")
        else:
            logger.error("Schema validation failed")
    finally:
        db.cleanup()

@cli.command()
def analyze():
    """Run graph analysis algorithms"""
    db = DatabaseManager()
    try:
        if db.run_graph_analysis():
            logger.info("Graph analysis completed successfully")
        else:
            logger.error("Graph analysis failed")
    finally:
        db.cleanup()

if __name__ == "__main__":
    cli()
