import os
import logging
import psycopg2
from neo4j import GraphDatabase
from typing import Dict, Any, Optional, List
from ..config.config import PG_CONN_STRING, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Set up logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.neo4j_driver = None
        self.connect()

    def connect(self):
        """Connect to both PostgreSQL and Neo4j databases"""
        try:
            # Connect to PostgreSQL first
            self.conn = psycopg2.connect(PG_CONN_STRING)
            logger.info("Connected to PostgreSQL")
            
            try:
                # Try Neo4j connection separately
                self.neo4j_driver = GraphDatabase.driver(
                    NEO4J_URI,
                    auth=(NEO4J_USER, NEO4J_PASSWORD)
                )
                # Test Neo4j connection with proper session handling
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 1")
                logger.info("Connected to Neo4j")
            except Exception as neo4j_error:
                logger.warning(f"Could not connect to Neo4j: {neo4j_error}")
                self.neo4j_driver = None
                # Don't raise - allow PostgreSQL-only operation
                
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

    def get_repository_info(self, repo_name: str) -> Dict[str, Any]:
        """Get repository information and statistics"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        rs.*,
                        (SELECT COUNT(*) FROM code_snippets cs 
                         WHERE cs.file_path LIKE %s) as snippet_count,
                        (SELECT COUNT(*) FROM active_sessions as_
                         WHERE as_.repository_name = rs.repository_name) as session_count
                    FROM repository_state rs
                    WHERE rs.repository_name = %s
                """, (f"%{repo_name}%", repo_name))
                
                result = cur.fetchone()
                if result:
                    return {
                        'name': result[1],
                        'url': result[2],
                        'last_analyzed': result[4],
                        'status': 'active' if result[5] else 'inactive',
                        'snippet_count': result[6],
                        'session_count': result[7]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting repository info: {str(e)}")
            return None

    def get_active_repositories(self, session_id: str = None) -> List[Dict[str, Any]]:
        """Get list of active repositories, optionally filtered by session"""
        try:
            with self.conn.cursor() as cur:
                if session_id:
                    cur.execute("""
                        SELECT DISTINCT r.repository_name, r.last_analyzed, r.is_current
                        FROM repository_state r
                        LEFT JOIN active_sessions s ON r.repository_name = s.repository_name
                        WHERE s.session_id = %s OR s.session_id IS NULL
                    """, (session_id,))
                else:
                    cur.execute("""
                        SELECT repository_name, last_analyzed, is_current
                        FROM repository_state
                    """)
                
                repos = []
                for row in cur.fetchall():
                    repos.append({
                        'name': row[0],
                        'last_analyzed': row[1],
                        'is_current': row[2]
                    })
                return repos
                
        except Exception as e:
            logger.error(f"Error getting active repositories: {e}")
            return []

    def show_schema(self):
        """Show current database schema"""
        try:
            with self.conn.cursor() as cur:
                # Show tables
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = cur.fetchall()
                print("\nTables:")
                for table in tables:
                    print(f"\n{table[0]}:")
                    # Show columns for each table
                    cur.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = %s
                    """, (table[0],))
                    columns = cur.fetchall()
                    for col in columns:
                        print(f"  - {col[0]}: {col[1]} (Nullable: {col[2]})")
                    
                    # Show foreign keys
                    cur.execute("""
                        SELECT
                            kcu.column_name,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name
                        FROM information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                            ON tc.constraint_name = kcu.constraint_name
                        JOIN information_schema.constraint_column_usage AS ccu
                            ON ccu.constraint_name = tc.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = %s
                    """, (table[0],))
                    foreign_keys = cur.fetchall()
                    if foreign_keys:
                        print("  Foreign Keys:")
                        for fk in foreign_keys:
                            print(f"    - {fk[0]} -> {fk[1]}.{fk[2]}")
                        
        except Exception as e:
            print(f"Error showing schema: {e}")

    def verify_database_state(self) -> List[str]:
        """Verify database tables and current repository state"""
        try:
            with self.conn.cursor() as cur:
                # Initialize tables if they don't exist
                self.initialize_tables()
                
                # Check tables exist
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [row[0] for row in cur.fetchall()]
                logger.info(f"Found tables: {tables}")

                # Check repository data
                cur.execute("SELECT repository_name, is_current FROM repository_state")
                repos = cur.fetchall()
                logger.info(f"Found repositories: {repos}")
                    
                # Check Neo4j connection state
                if self.neo4j_driver:
                    logger.info("Neo4j connection is available")
                else:
                    logger.warning("Neo4j connection is not available")
                    
                return tables
                
        except Exception as e:
            logger.error(f"Error verifying database state: {e}")
            return []

    def init_schema(self):
        """Initialize or update database schema"""
        try:
            with self.conn.cursor() as cur:
                # Add repository_name column if it doesn't exist
                cur.execute("""
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = 'code_snippets' 
                            AND column_name = 'repository_name'
                        ) THEN
                            ALTER TABLE code_snippets 
                            ADD COLUMN repository_name text REFERENCES repository_state(repository_name);
                        END IF;
                    END $$;
                """)
                self.conn.commit()
                logger.info("Schema updated successfully")
        except Exception as e:
            logger.error(f"Error updating schema: {e}")
            self.conn.rollback()

    def initialize_tables(self):
        """Initialize database tables if they don't exist"""
        try:
            with self.conn.cursor() as cur:
                # Drop existing tables in correct order
                cur.execute("""
                    DROP TABLE IF EXISTS active_sessions CASCADE;
                    DROP TABLE IF EXISTS code_snippets CASCADE;
                    DROP TABLE IF EXISTS repository_state CASCADE;
                """)
                
                # Create repository state table
                cur.execute("""
                    CREATE TABLE repository_state (
                        id SERIAL PRIMARY KEY,
                        repository_name TEXT UNIQUE NOT NULL,
                        repository_url TEXT,
                        local_path TEXT,
                        last_analyzed TIMESTAMP,
                        is_current BOOLEAN DEFAULT false
                    );
                    
                    CREATE TABLE active_sessions (
                        id SERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        repository_name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (repository_name) REFERENCES repository_state(repository_name)
                    );
                    
                    CREATE TABLE code_snippets (
                        id SERIAL PRIMARY KEY,
                        repository_name TEXT REFERENCES repository_state(repository_name),
                        file_path TEXT NOT NULL,
                        content TEXT NOT NULL,
                        embedding VECTOR(384),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Create indexes for performance
                    CREATE INDEX IF NOT EXISTS idx_repo_name ON repository_state(repository_name);
                    CREATE INDEX IF NOT EXISTS idx_session_repo ON active_sessions(repository_name);
                    CREATE INDEX IF NOT EXISTS idx_snippets_repo ON code_snippets(repository_name);
                """)
                
                self.conn.commit()
                logger.info("Database tables initialized")
                
        except Exception as e:
            logger.error(f"Error initializing tables: {e}")
            self.conn.rollback()
            raise
