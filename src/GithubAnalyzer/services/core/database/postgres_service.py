from typing import Optional, List, Dict, Any, Tuple, Set
import psycopg2
import json
from datetime import datetime
from psycopg2.extras import execute_values
import numpy as np

from GithubAnalyzer.services.core.database.embedding_service import CodeEmbeddingService
from psycopg2.extensions import connection
from GithubAnalyzer.services.core.database.db_config import get_postgres_config
from GithubAnalyzer.models.core.database import CodeSnippet
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

class PostgresService:
    def __init__(self):
        self._conn: Optional[connection] = None
        self._config = get_postgres_config()
        self._embedding_service = CodeEmbeddingService()
        self.connect()  # Auto-connect on initialization

    def connect(self) -> None:
        """Establish connection to PostgreSQL database."""
        if not self._conn or self._conn.closed:
            self._conn = psycopg2.connect(**self._config)

    def ensure_connection(self) -> None:
        """Ensure we have an active connection."""
        if not self._conn or self._conn.closed:
            self.connect()

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()

    def setup_vector_extension(self) -> None:
        """Setup pgvector extension for code embeddings."""
        self.ensure_connection()
        with self._conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS vector;')
            self._conn.commit()

    def drop_tables(self) -> None:
        """Drop existing tables."""
        self.ensure_connection()
        with self._conn.cursor() as cur:
            cur.execute('''
                DROP TABLE IF EXISTS code_snippets CASCADE;
                DROP TABLE IF EXISTS functions CASCADE;
                DROP TABLE IF EXISTS classes CASCADE;
                DROP TABLE IF EXISTS comments CASCADE;
                DROP TABLE IF EXISTS repositories CASCADE;
            ''')
            self._conn.commit()

    def create_tables(self) -> None:
        """Create necessary tables for code storage with vector embeddings."""
        self.ensure_connection()
        with self._conn.cursor() as cur:
            # Drop existing tables if they exist
            cur.execute('DROP TABLE IF EXISTS code_snippets CASCADE;')
            cur.execute('DROP TABLE IF EXISTS repositories CASCADE;')
            cur.execute('DROP TABLE IF EXISTS functions CASCADE;')
            cur.execute('DROP TABLE IF EXISTS classes CASCADE;')
            cur.execute('DROP TABLE IF EXISTS comments CASCADE;')
            self._conn.commit()
            
            # Enable vector extension
            cur.execute('CREATE EXTENSION IF NOT EXISTS vector;')
            self._conn.commit()
            
            # Repositories table
            cur.execute('''
                CREATE TABLE repositories (
                    id SERIAL PRIMARY KEY,
                    repo_url TEXT NOT NULL UNIQUE,
                    repo_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            self._conn.commit()
            
            # Code snippets table with vector embeddings and metadata
            cur.execute('''
                CREATE TABLE code_snippets (
                    id SERIAL PRIMARY KEY,
                    repo_id INTEGER REFERENCES repositories(id),
                    file_path TEXT NOT NULL,
                    code_text TEXT NOT NULL,
                    language TEXT NOT NULL,
                    embedding VECTOR(768),
                    metadata JSONB DEFAULT NULL,
                    is_supported BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            self._conn.commit()
            
            # Add language constraint
            cur.execute('''
                ALTER TABLE code_snippets
                ADD CONSTRAINT valid_language CHECK (language IN (
                    'python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'go', 'rust',
                    'ruby', 'php', 'html', 'css', 'markdown', 'yaml', 'json', 'toml', 'xml',
                    'dockerfile', 'makefile', 'gitignore', 'requirements', 'plaintext', 'toml'
                ));
            ''')
            self._conn.commit()
            
            # Add metadata constraint
            cur.execute('''
                ALTER TABLE code_snippets
                ADD CONSTRAINT valid_metadata 
                CHECK (metadata IS NULL OR jsonb_typeof(metadata) = 'object');
            ''')
            self._conn.commit()
            
            # Create indexes
            cur.execute('CREATE INDEX idx_code_snippets_language ON code_snippets(language);')
            cur.execute('CREATE INDEX idx_code_snippets_supported ON code_snippets(is_supported);')
            cur.execute('CREATE INDEX idx_code_snippets_metadata ON code_snippets USING gin(metadata);')
            self._conn.commit()
            
            # Functions table
            cur.execute('''
                CREATE TABLE functions (
                    id SERIAL PRIMARY KEY,
                    repo_id INTEGER REFERENCES repositories(id),
                    file_path TEXT NOT NULL,
                    name TEXT NOT NULL,
                    language TEXT NOT NULL,
                    metadata JSONB,
                    start_point JSONB,
                    end_point JSONB,
                    docstring TEXT,
                    docstring_embedding vector(768),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            self._conn.commit()
            
            # Add position constraint
            cur.execute('''
                ALTER TABLE functions
                ADD CONSTRAINT valid_position CHECK (
                    start_point IS NULL OR (
                        jsonb_typeof(start_point) = 'object' AND
                        start_point ? 'line' AND
                        start_point ? 'character'
                    )
                );
            ''')
            self._conn.commit()
            
            # Create function indexes
            cur.execute('CREATE INDEX idx_functions_language ON functions(language);')
            cur.execute('CREATE INDEX idx_functions_name ON functions(name);')
            cur.execute('CREATE INDEX idx_functions_metadata ON functions USING gin(metadata);')
            self._conn.commit()
            
            # Classes table
            cur.execute('''
                CREATE TABLE classes (
                    id SERIAL PRIMARY KEY,
                    repo_id INTEGER REFERENCES repositories(id),
                    file_path TEXT NOT NULL,
                    name TEXT NOT NULL,
                    docstring TEXT,
                    docstring_embedding vector(768),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            self._conn.commit()
            
            # Comments table
            cur.execute('''
                CREATE TABLE comments (
                    id SERIAL PRIMARY KEY,
                    repo_id INTEGER REFERENCES repositories(id),
                    file_path TEXT NOT NULL,
                    comment_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(768),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            self._conn.commit()

    def store_code_with_embedding(self, snippet: CodeSnippet) -> None:
        """Store code snippet with its embedding vector and metadata."""
        self.ensure_connection()
        try:
            embedding = self._embedding_service.get_embedding(snippet.code_text)
            
            with self._conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO code_snippets (
                        repo_id, file_path, code_text, language, embedding, 
                        metadata, is_supported, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    snippet.repo_id,
                    snippet.file_path,
                    snippet.code_text,
                    snippet.language,
                    embedding,
                    json.dumps(snippet.metadata) if hasattr(snippet, 'metadata') else None,
                    snippet.metadata.get('is_supported', True) if hasattr(snippet, 'metadata') else True,
                    snippet.created_at
                ))
                self._conn.commit()
                
                logger.debug({
                    "message": "Stored code snippet",
                    "context": {
                        "file_path": snippet.file_path,
                        "language": snippet.language,
                        "has_embedding": bool(embedding),
                        "has_metadata": hasattr(snippet, 'metadata')
                    }
                })
        except Exception as e:
            logger.error({
                "message": "Failed to store code snippet",
                "context": {
                    "file_path": snippet.file_path,
                    "error": str(e)
                }
            })
            self._conn.rollback()
            raise

    def find_similar_code(self, query: str, language: Optional[str] = None,
                         limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar code snippets using vector similarity search."""
        self.ensure_connection()
        query_embedding = self._embedding_service.get_embedding(query)
        
        with self._conn.cursor() as cur:
            # Build query with optional language filter
            query_sql = '''
                SELECT 
                    file_path,
                    code_text,
                    language,
                    metadata,
                    1 - (embedding <=> %s::vector) as similarity
                FROM code_snippets
                WHERE is_supported = true
            '''
            params = [query_embedding]
            
            if language:
                query_sql += ' AND language = %s'
                params.append(language)
                
            query_sql += '''
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            '''
            params.extend([query_embedding, limit])
            
            cur.execute(query_sql, params)
            
            return [
                {
                    'file_path': row[0],
                    'code_text': row[1],
                    'language': row[2],
                    'metadata': row[3],
                    'similarity': row[4]
                }
                for row in cur.fetchall()
            ]

    def batch_store_code(self, code_entries: List[Tuple[int, str, str, str, Optional[Dict[str, Any]], bool]]) -> None:
        """Store multiple code snippets with their embeddings in batch.
        
        Args:
            code_entries: List of tuples containing (repo_id: int, file_path: str, code_text: str, language: str, metadata: Optional[Dict], is_supported: bool)
        """
        self.ensure_connection()
        code_texts = [entry[2] for entry in code_entries]
        embeddings = self._embedding_service.get_embeddings(code_texts)
        
        with self._conn.cursor() as cur:
            for (repo_id, file_path, code_text, language, metadata, is_supported), embedding in zip(code_entries, embeddings):
                # Use empty string for unsupported languages
                language = language or ""
                
                cur.execute('''
                    INSERT INTO code_snippets (
                        repo_id, file_path, code_text, language, embedding, metadata, is_supported
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    repo_id, 
                    file_path, 
                    code_text, 
                    language,
                    embedding,
                    json.dumps(metadata) if metadata else None,
                    is_supported
                ))
            self._conn.commit()

    def create_repository(self, repo_url: str) -> int:
        """Create a new repository entry.
        
        Args:
            repo_url: URL of the GitHub repository
            
        Returns:
            Repository ID as integer
        """
        self.ensure_connection()
        with self._conn.cursor() as cur:
            # Extract repo name from URL
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            
            # Check if repository already exists
            cur.execute('''
                SELECT id FROM repositories
                WHERE repo_url = %s
            ''', (repo_url,))
            
            existing = cur.fetchone()
            if existing:
                return existing[0]
            
            # Create new repository
            cur.execute('''
                INSERT INTO repositories (repo_url, repo_name)
                VALUES (%s, %s)
                RETURNING id
            ''', (repo_url, repo_name))
            
            repo_id = cur.fetchone()[0]
            self._conn.commit()
            return repo_id

    def semantic_search(self, query: str, limit: int = 5, 
                       filter_repo: Optional[str] = None) -> List[Dict[str, Any]]:
        """Semantic search across code, docstrings, and comments."""
        self.ensure_connection()
        query_embedding = self._embedding_service.get_embedding(query)
        
        with self._conn.cursor() as cur:
            # Search in code snippets
            filter_clause = "WHERE repo_id = %s" if filter_repo else ""
            cur.execute(f'''
                WITH ranked_snippets AS (
                    SELECT 
                        cs.id,
                        cs.file_path,
                        cs.code_text as content,
                        1 - (cs.embedding <=> %s::vector) as similarity
                    FROM code_snippets cs
                    {filter_clause}
                    ORDER BY cs.embedding <=> %s::vector
                    LIMIT %s
                )
                SELECT * FROM ranked_snippets
                WHERE similarity > 0.7
            ''', (query_embedding, query_embedding, limit))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'file_path': row[1],
                    'content': row[2],
                    'similarity': row[3]
                })
            
            return results

    def get_code_context(self, file_path: str, line_number: int) -> Dict[str, Any]:
        """Get comprehensive context for a code location."""
        self.ensure_connection()
        with self._conn.cursor() as cur:
            cur.execute('''
                WITH target_snippet AS (
                    SELECT id, content
                    FROM code_snippets
                    WHERE file_path = %s
                    AND start_line <= %s
                    AND end_line >= %s
                )
                SELECT 
                    ts.content as code,
                    f.name as function_name,
                    f.docstring as function_doc,
                    c.name as class_name,
                    c.docstring as class_doc,
                    array_agg(cm.content) as comments
                FROM target_snippet ts
                LEFT JOIN functions f ON ts.id = f.code_snippet_id
                LEFT JOIN classes c ON ts.id = c.code_snippet_id
                LEFT JOIN comments cm ON ts.id = cm.code_snippet_id
                GROUP BY ts.id, ts.content, f.name, f.docstring, c.name, c.docstring
            ''', (file_path, line_number, line_number))
            
            row = cur.fetchone()
            if not row:
                return {}
                
            return {
                'code': row[0],
                'function': {'name': row[1], 'docstring': row[2]},
                'class': {'name': row[3], 'docstring': row[4]},
                'comments': row[5] or []
            }

    def get_documentation_context(self, query: str) -> Dict[str, Any]:
        """Get documentation context for a query."""
        self.ensure_connection()
        query_embedding = self._embedding_service.get_embedding(query)
        
        with self._conn.cursor() as cur:
            # Search in docstrings and comments
            cur.execute('''
                WITH doc_matches AS (
                    SELECT 
                        'function' as type,
                        name,
                        docstring as content,
                        1 - (docstring_embedding <=> %s) as similarity
                    FROM functions
                    WHERE docstring IS NOT NULL
                    UNION ALL
                    SELECT 
                        'class' as type,
                        name,
                        docstring as content,
                        1 - (docstring_embedding <=> %s) as similarity
                    FROM classes
                    WHERE docstring IS NOT NULL
                    UNION ALL
                    SELECT 
                        'comment' as type,
                        comment_type as name,
                        content,
                        1 - (embedding <=> %s) as similarity
                    FROM comments
                    ORDER BY similarity DESC
                    LIMIT 10
                )
                SELECT * FROM doc_matches
                WHERE similarity > 0.7
            ''', (query_embedding, query_embedding, query_embedding))
            
            results = {
                'docstrings': [],
                'comments': [],
                'examples': []
            }
            
            for row in cur.fetchall():
                item = {
                    'type': row[0],
                    'name': row[1],
                    'content': row[2],
                    'similarity': row[3]
                }
                
                if row[0] in ('function', 'class'):
                    results['docstrings'].append(item)
                else:
                    results['comments'].append(item)
            
            return results

    def get_all_code_snippets(self) -> List[Dict[str, Any]]:
        """Get all code snippets from the database."""
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT file_path, language, metadata, is_supported
                FROM code_snippets
            """)
            return [
                {
                    'file_path': row[0],
                    'language': row[1],
                    'metadata': row[2],
                    'is_supported': row[3]
                }
                for row in cur.fetchall()
            ]
            
    def delete_file_snippets(self, file_path: str) -> None:
        """Delete all code snippets related to a file.
        
        Args:
            file_path: Path to the file
        """
        with self._conn.cursor() as cur:
            cur.execute("""
                DELETE FROM code_snippets
                WHERE file_path = %s
            """, (file_path,))
            self._conn.commit()
            
    def get_languages(self) -> Set[str]:
        """Get all languages present in the database."""
        self.ensure_connection()
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT language
                FROM code_snippets
                WHERE language IS NOT NULL
            """)
            return {row[0] for row in cur.fetchall()}
            
    def update_file_language(self, file_path: str, language: str) -> None:
        """Update the language of all code snippets for a file.
        
        Args:
            file_path: Path to the file
            language: New language identifier
        """
        self.ensure_connection()
        with self._conn.cursor() as cur:
            cur.execute("""
                UPDATE code_snippets
                SET language = %s
                WHERE file_path = %s
            """, (language, file_path))
            self._conn.commit()

    def update_ast_relationships(self, file_path: str, relationships: Dict[str, Any]) -> None:
        """Update AST relationships in code snippets.
        
        Args:
            file_path: Path to the file
            relationships: Dictionary of relationships from Neo4j
        """
        self.ensure_connection()
        with self._conn.cursor() as cur:
            # Get current metadata
            cur.execute('''
                SELECT metadata
                FROM code_snippets
                WHERE file_path = %s
            ''', (file_path,))
            
            row = cur.fetchone()
            if not row or not row[0]:
                return
                
            metadata = json.loads(row[0])
            
            # Update relationships in metadata
            if 'elements' in metadata:
                for element_type, elements in metadata['elements'].items():
                    for element in elements:
                        if element['name'] in relationships:
                            element['relationships'] = relationships[element['name']]
                            
            # Store updated metadata
            cur.execute('''
                UPDATE code_snippets
                SET metadata = %s
                WHERE file_path = %s
            ''', (json.dumps(metadata), file_path))
            
            self._conn.commit()
            
    def delete_code_snippet(self, repo_id: str, file_path: str) -> None:
        """Delete a code snippet and its related data.
        
        Args:
            repo_id: Repository identifier
            file_path: Path to the file
        """
        with self._conn.cursor() as cur:
            # Delete from code_snippets
            cur.execute('''
                DELETE FROM code_snippets
                WHERE repo_id = %s AND file_path = %s
            ''', (repo_id, file_path))
            
            # Delete from functions
            cur.execute('''
                DELETE FROM functions
                WHERE repo_id = %s AND file_path = %s
            ''', (repo_id, file_path))
            
            # Delete from classes
            cur.execute('''
                DELETE FROM classes
                WHERE repo_id = %s AND file_path = %s
            ''', (repo_id, file_path))
            
            self._conn.commit()
            
    def update_code_snippet(self, repo_id: str, file_path: str, code_text: str,
                          language: str, metadata: Dict[str, Any]) -> None:
        """Update a code snippet with new data.
        
        Args:
            repo_id: Repository identifier
            file_path: Path to the file
            code_text: New code content
            language: Programming language
            metadata: New metadata
        """
        embedding = self._embedding_service.get_embedding(code_text)
        
        with self._conn.cursor() as cur:
            # Update code snippet
            cur.execute('''
                UPDATE code_snippets
                SET code_text = %s,
                    language = %s,
                    embedding = %s,
                    metadata = %s,
                    is_supported = %s
                WHERE repo_id = %s AND file_path = %s
            ''', (
                code_text,
                language,
                embedding,
                json.dumps(metadata),
                metadata.get('is_supported', True),
                repo_id,
                file_path
            ))
            
            # Update functions
            if 'elements' in metadata and 'function' in metadata['elements']:
                # First delete old functions
                cur.execute('''
                    DELETE FROM functions
                    WHERE repo_id = %s AND file_path = %s
                ''', (repo_id, file_path))
                
                # Then insert new ones
                for func in metadata['elements']['function']:
                    cur.execute('''
                        INSERT INTO functions (
                            repo_id, file_path, name, language,
                            metadata, start_point, end_point
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        repo_id,
                        file_path,
                        func['name'],
                        language,
                        json.dumps(func),
                        json.dumps(func['start_point']),
                        json.dumps(func['end_point'])
                    ))
            
            self._conn.commit()

    def get_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories in the database.
        
        Returns:
            List of dictionaries containing repository information
        """
        self.ensure_connection()
        with self._conn.cursor() as cur:
            cur.execute('''
                SELECT id, repo_url, repo_name, created_at
                FROM repositories
            ''')
            rows = cur.fetchall()
            return [
                {
                    'id': row[0],
                    'url': row[1],
                    'name': row[2],
                    'created_at': row[3]
                }
                for row in rows
            ]

    def get_file_count(self, repo_id: Optional[int] = None) -> int:
        """Get the total number of files stored.
        
        Args:
            repo_id: Optional repository ID to filter by
            
        Returns:
            Number of files stored
        """
        query = "SELECT COUNT(*) FROM code_snippets"
        if repo_id:
            query += " WHERE repo_id = %s"
            return self._execute_query(query, (repo_id,))[0][0]
        return self._execute_query(query)[0][0]
        
    def get_language_statistics(self, repo_id: Optional[int] = None) -> Dict[str, int]:
        """Get breakdown of files by language.
        
        Args:
            repo_id: Optional repository ID to filter by
            
        Returns:
            Dictionary mapping languages to file counts
        """
        query = "SELECT language, COUNT(*) FROM code_snippets"
        if repo_id:
            query += " WHERE repo_id = %s"
            query += " GROUP BY language"
            rows = self._execute_query(query, (repo_id,))
        else:
            query += " GROUP BY language"
            rows = self._execute_query(query)
            
        return {row[0]: row[1] for row in rows}
        
    def get_recent_files(self, limit: int = 5, repo_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get most recently added files.
        
        Args:
            limit: Maximum number of files to return
            repo_id: Optional repository ID to filter by
            
        Returns:
            List of recent file entries
        """
        query = """
            SELECT file_path, language, created_at 
            FROM code_snippets
        """
        if repo_id:
            query += " WHERE repo_id = %s"
            query += " ORDER BY created_at DESC LIMIT %s"
            rows = self._execute_query(query, (repo_id, limit))
        else:
            query += " ORDER BY created_at DESC LIMIT %s"
            rows = self._execute_query(query, (limit,))
            
        return [
            {
                'file_path': row[0],
                'language': row[1],
                'created_at': row[2]
            }
            for row in rows
        ]

    def _execute_query(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Execute a PostgreSQL query.
        
        Args:
            query: SQL query to execute
            params: Optional query parameters
            
        Returns:
            List of result rows
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            with self._conn.cursor() as cur:
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                    
                if query.strip().upper().startswith('SELECT'):
                    return cur.fetchall()
                return []
                
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            self._conn.rollback()
            raise

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect() 