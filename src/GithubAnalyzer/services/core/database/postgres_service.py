from typing import Optional, List, Dict, Any, Tuple, Set
import psycopg2
import json
from datetime import datetime
from psycopg2.extras import execute_values
import numpy as np
import time
import threading
from dataclasses import dataclass
from pathlib import Path

from GithubAnalyzer.services.core.database.embedding_service import CodeEmbeddingService
from psycopg2.extensions import connection
from GithubAnalyzer.services.core.database.db_config import get_postgres_config
from GithubAnalyzer.models.core.database import CodeSnippet
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger("core.database.postgres")

@dataclass
class PostgresService:
    def __post_init__(self):
        """Initialize the PostgreSQL service."""
        self._conn: Optional[connection] = None
        self._config = get_postgres_config()
        self._embedding_service = CodeEmbeddingService()
        self._start_time = time.time()
        self.connect()  # Auto-connect on initialization

    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """Get standardized logging context."""
        context = {
            'module': 'postgres_service',
            'thread': threading.get_ident(),
            'duration_ms': int((time.time() - self._start_time) * 1000),
        }
        context.update(kwargs)
        return context

    def _log(self, level: str, message: str, **kwargs):
        """Log with consistent context."""
        context = self._get_context(**kwargs)
        getattr(logger, level)(message, extra={'context': context})

    def connect(self) -> None:
        """Establish connection to PostgreSQL database."""
        try:
            if not self._conn or self._conn.closed:
                self._conn = psycopg2.connect(**self._config)
                self._log('info', 'Connected to PostgreSQL database', 
                         host=self._config.get('host'),
                         port=self._config.get('port'),
                         database=self._config.get('database'))
        except Exception as e:
            self._log('error', 'Failed to connect to PostgreSQL database',
                     error=str(e),
                     host=self._config.get('host'),
                     port=self._config.get('port'))
            raise

    def ensure_connection(self) -> None:
        """Ensure we have an active connection."""
        if not self._conn or self._conn.closed:
            self._log('debug', 'Reconnecting to database')
            self.connect()

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._log('info', 'Disconnected from PostgreSQL database')

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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS repositories (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    resource_type TEXT NOT NULL CHECK (resource_type IN ('codebase', 'documentation')),
                    repo_name TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._conn.commit()
            
            # Code snippets table with vector embeddings and metadata
            cur.execute('''
                CREATE TABLE code_snippets (
                    id SERIAL PRIMARY KEY,
                    repo_id INTEGER REFERENCES repositories(id),
                    file_path TEXT NOT NULL,
                    code_text TEXT NOT NULL,
                    language TEXT NOT NULL,
                    syntax_valid BOOLEAN DEFAULT true,
                    ast_data JSONB DEFAULT NULL,
                    complexity_metrics JSONB DEFAULT NULL,
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
        start_time = time.time()
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
                
                self._log('debug', 'Stored code snippet',
                         file_path=snippet.file_path,
                         language=snippet.language,
                         has_embedding=bool(embedding),
                         has_metadata=hasattr(snippet, 'metadata'),
                         duration_ms=int((time.time() - start_time) * 1000))
        except Exception as e:
            self._log('error', 'Failed to store code snippet',
                     file_path=snippet.file_path,
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            self._conn.rollback()
            raise

    def find_similar_code(self, query: str, language: Optional[str] = None,
                         limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar code snippets using vector similarity search."""
        start_time = time.time()
        self.ensure_connection()
        try:
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
                
                query_sql += ' ORDER BY similarity DESC LIMIT %s'
                params.append(limit)
                
                cur.execute(query_sql, params)
                results = cur.fetchall()
                
                self._log('debug', 'Found similar code snippets',
                         query_length=len(query),
                         language=language,
                         result_count=len(results),
                         duration_ms=int((time.time() - start_time) * 1000))
                
                return [
                    {
                        'file_path': r[0],
                        'code_text': r[1],
                        'language': r[2],
                        'metadata': r[3],
                        'similarity': float(r[4])
                    }
                    for r in results
                ]
        except Exception as e:
            self._log('error', 'Failed to find similar code',
                     query_length=len(query),
                     language=language,
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

    def batch_store_code(self, code_entries: List[Tuple[int, str, str, str, Optional[Dict[str, Any]], bool]]) -> None:
        """Batch store code snippets with embeddings."""
        start_time = time.time()
        if not code_entries:
            self._log('debug', 'No code entries to store')
            return

        self.ensure_connection()
        try:
            # Process embeddings in batches
            processed_entries = []
            for repo_id, file_path, code_text, language, metadata, is_supported in code_entries:
                embedding = self._embedding_service.get_embedding(code_text)
                processed_entries.append((
                    repo_id, file_path, code_text, language, embedding,
                    json.dumps(metadata) if metadata else None,
                    is_supported, datetime.now()
                ))

            with self._conn.cursor() as cur:
                execute_values(cur, '''
                    INSERT INTO code_snippets (
                        repo_id, file_path, code_text, language, embedding,
                        metadata, is_supported, created_at
                    ) VALUES %s
                ''', processed_entries)
                self._conn.commit()
                
                self._log('info', 'Batch stored code snippets',
                         entry_count=len(code_entries),
                         duration_ms=int((time.time() - start_time) * 1000))
        except Exception as e:
            self._log('error', 'Failed to batch store code snippets',
                     entry_count=len(code_entries),
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            self._conn.rollback()
            raise

    def create_repository(self, url: str, resource_type: str = 'codebase', name: Optional[str] = None, description: Optional[str] = None) -> int:
        """Create a new repository entry.
        
        Args:
            url: URL or file path to the repository/documentation
            resource_type: Type of resource ('codebase' or 'documentation')
            name: Optional name for the resource
            description: Optional description
            
        Returns:
            Repository ID
        """
        with self._conn.cursor() as cur:
            # Check if repository already exists
            cur.execute(
                "SELECT id FROM repositories WHERE url = %s AND resource_type = %s",
                (url, resource_type)
            )
            existing = cur.fetchone()
            if existing:
                return int(existing[0])
                
            # If no name provided, use last part of URL for codebase
            if not name and resource_type == 'codebase':
                name = Path(url.replace("file://", "")).name
                
            # Create new repository
            cur.execute("""
                INSERT INTO repositories (url, resource_type, repo_name, description)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (url, resource_type, name, description))
            
            repo_id = cur.fetchone()[0]
            self._conn.commit()
            return int(repo_id)

    def semantic_search(self, query: str, limit: int = 5, 
                       filter_repo: Optional[str] = None) -> List[Dict[str, Any]]:
        """Perform semantic search over code snippets."""
        start_time = time.time()
        self.ensure_connection()
        try:
            query_embedding = self._embedding_service.get_embedding(query)
            
            with self._conn.cursor() as cur:
                # Build query with optional repo filter
                query_sql = '''
                    SELECT 
                        cs.file_path,
                        cs.code_text,
                        cs.language,
                        cs.metadata,
                        r.repo_url,
                        1 - (cs.embedding <=> %s::vector) as similarity
                    FROM code_snippets cs
                    JOIN repositories r ON cs.repo_id = r.id
                    WHERE cs.is_supported = true
                '''
                params = [query_embedding]
                
                if filter_repo:
                    query_sql += ' AND r.repo_url = %s'
                    params.append(filter_repo)
                
                query_sql += ' ORDER BY similarity DESC LIMIT %s'
                params.append(limit)
                
                cur.execute(query_sql, params)
                results = cur.fetchall()
                
                self._log('debug', 'Performed semantic search',
                         query_length=len(query),
                         filter_repo=filter_repo,
                         result_count=len(results),
                         duration_ms=int((time.time() - start_time) * 1000))
                
                return [
                    {
                        'file_path': r[0],
                        'code_text': r[1],
                        'language': r[2],
                        'metadata': r[3],
                        'repo_url': r[4],
                        'similarity': float(r[5])
                    }
                    for r in results
                ]
        except Exception as e:
            self._log('error', 'Failed to perform semantic search',
                     query_length=len(query),
                     filter_repo=filter_repo,
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

    def get_code_context(self, file_path: str, line_number: int) -> Dict[str, Any]:
        """Get context around a specific line of code."""
        start_time = time.time()
        self.ensure_connection()
        try:
            with self._conn.cursor() as cur:
                cur.execute('''
                    SELECT code_text, language, metadata
                    FROM code_snippets
                    WHERE file_path = %s
                    LIMIT 1
                ''', (file_path,))
                result = cur.fetchone()
                
                if not result:
                    self._log('warning', 'No code context found',
                             file_path=file_path,
                             line_number=line_number,
                             duration_ms=int((time.time() - start_time) * 1000))
                    return {}
                
                code_text, language, metadata = result
                lines = code_text.split('\n')
                
                # Get context window
                start_line = max(0, line_number - 5)
                end_line = min(len(lines), line_number + 5)
                context_lines = lines[start_line:end_line]
                
                self._log('debug', 'Retrieved code context',
                         file_path=file_path,
                         line_number=line_number,
                         context_size=len(context_lines),
                         duration_ms=int((time.time() - start_time) * 1000))
                
                return {
                    'code_context': '\n'.join(context_lines),
                    'start_line': start_line,
                    'end_line': end_line,
                    'language': language,
                    'metadata': metadata
                }
        except Exception as e:
            self._log('error', 'Failed to get code context',
                     file_path=file_path,
                     line_number=line_number,
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

    def get_documentation_context(self, query: str) -> Dict[str, Any]:
        """Get documentation context for a query."""
        start_time = time.time()
        self.ensure_connection()
        try:
            query_embedding = self._embedding_service.get_embedding(query)
            
            with self._conn.cursor() as cur:
                # Search in functions
                cur.execute('''
                    SELECT 
                        f.name,
                        f.docstring,
                        f.file_path,
                        f.language,
                        1 - (f.docstring_embedding <=> %s::vector) as similarity
                    FROM functions f
                    WHERE f.docstring IS NOT NULL
                    ORDER BY similarity DESC
                    LIMIT 5
                ''', (query_embedding,))
                function_results = cur.fetchall()
                
                # Search in classes
                cur.execute('''
                    SELECT 
                        c.name,
                        c.docstring,
                        c.file_path,
                        1 - (c.docstring_embedding <=> %s::vector) as similarity
                    FROM classes c
                    WHERE c.docstring IS NOT NULL
                    ORDER BY similarity DESC
                    LIMIT 5
                ''', (query_embedding,))
                class_results = cur.fetchall()
                
                # Search in comments
                cur.execute('''
                    SELECT 
                        cm.comment_type,
                        cm.content,
                        cm.file_path,
                        1 - (cm.embedding <=> %s::vector) as similarity
                    FROM comments cm
                    ORDER BY similarity DESC
                    LIMIT 5
                ''', (query_embedding,))
                comment_results = cur.fetchall()
                
                self._log('debug', 'Retrieved documentation context',
                         query_length=len(query),
                         function_count=len(function_results),
                         class_count=len(class_results),
                         comment_count=len(comment_results),
                         duration_ms=int((time.time() - start_time) * 1000))
                
                return {
                    'functions': [
                        {
                            'name': r[0],
                            'docstring': r[1],
                            'file_path': r[2],
                            'language': r[3],
                            'similarity': float(r[4])
                        }
                        for r in function_results
                    ],
                    'classes': [
                        {
                            'name': r[0],
                            'docstring': r[1],
                            'file_path': r[2],
                            'similarity': float(r[3])
                        }
                        for r in class_results
                    ],
                    'comments': [
                        {
                            'type': r[0],
                            'content': r[1],
                            'file_path': r[2],
                            'similarity': float(r[3])
                        }
                        for r in comment_results
                    ]
                }
        except Exception as e:
            self._log('error', 'Failed to get documentation context',
                     query_length=len(query),
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

    def get_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories."""
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT id, url, resource_type, repo_name, description, 
                       created_at, updated_at
                FROM repositories
            """)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get_all_code_snippets(self) -> List[Dict[str, Any]]:
        """Get all code snippets from the database.
        
        Returns:
            List of dictionaries containing code snippet information
        """
        self.ensure_connection()
        with self._conn.cursor() as cur:
            cur.execute('''
                SELECT id, repo_id, file_path, code_text, language, syntax_valid,
                       ast_data, complexity_metrics, embedding, created_at
                FROM code_snippets
            ''')
            columns = [desc[0] for desc in cur.description]
            snippets = [dict(zip(columns, row)) for row in cur.fetchall()]
            
            self._log('debug', f'Retrieved {len(snippets)} code snippets')
            return snippets

    def delete_file_snippets(self, file_path: str) -> None:
        """Delete all code snippets for a given file path."""
        start_time = time.time()
        self.ensure_connection()
        try:
            with self._conn.cursor() as cur:
                cur.execute('DELETE FROM code_snippets WHERE file_path = %s', (file_path,))
                deleted_count = cur.rowcount
                self._conn.commit()
                
                self._log('info', 'Deleted file snippets',
                         file_path=file_path,
                         deleted_count=deleted_count,
                         duration_ms=int((time.time() - start_time) * 1000))
        except Exception as e:
            self._log('error', 'Failed to delete file snippets',
                     file_path=file_path,
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            self._conn.rollback()
            raise

    def get_languages(self) -> Set[str]:
        """Get all unique languages in the database."""
        start_time = time.time()
        self.ensure_connection()
        try:
            with self._conn.cursor() as cur:
                cur.execute('SELECT DISTINCT language FROM code_snippets WHERE language IS NOT NULL')
                languages = {row[0] for row in cur.fetchall()}
                
                self._log('debug', 'Retrieved unique languages',
                         language_count=len(languages),
                         duration_ms=int((time.time() - start_time) * 1000))
                return languages
        except Exception as e:
            self._log('error', 'Failed to retrieve languages',
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

    def update_file_language(self, file_path: str, language: str) -> None:
        """Update the language of a file's code snippets."""
        start_time = time.time()
        self.ensure_connection()
        try:
            with self._conn.cursor() as cur:
                cur.execute('''
                    UPDATE code_snippets 
                    SET language = %s
                    WHERE file_path = %s
                ''', (language, file_path))
                updated_count = cur.rowcount
                self._conn.commit()
                
                self._log('info', 'Updated file language',
                         file_path=file_path,
                         language=language,
                         updated_count=updated_count,
                         duration_ms=int((time.time() - start_time) * 1000))
        except Exception as e:
            self._log('error', 'Failed to update file language',
                     file_path=file_path,
                     language=language,
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            self._conn.rollback()
            raise

    def update_ast_relationships(self, file_path: str, relationships: Dict[str, Any]) -> None:
        """Update AST relationships for a file."""
        start_time = time.time()
        self.ensure_connection()
        try:
            with self._conn.cursor() as cur:
                # Update functions
                if 'functions' in relationships:
                    for func in relationships['functions']:
                        cur.execute('''
                            INSERT INTO functions (
                                repo_id, file_path, name, language, metadata,
                                start_point, end_point, docstring
                            )
                            VALUES (
                                (SELECT repo_id FROM code_snippets WHERE file_path = %s LIMIT 1),
                                %s, %s, %s, %s, %s, %s, %s
                            )
                            ON CONFLICT (file_path, name) DO UPDATE
                            SET metadata = EXCLUDED.metadata,
                                start_point = EXCLUDED.start_point,
                                end_point = EXCLUDED.end_point,
                                docstring = EXCLUDED.docstring
                        ''', (
                            file_path, file_path, func['name'], func.get('language'),
                            json.dumps(func.get('metadata')), json.dumps(func.get('start_point')),
                            json.dumps(func.get('end_point')), func.get('docstring')
                        ))
                
                # Update classes
                if 'classes' in relationships:
                    for cls in relationships['classes']:
                        cur.execute('''
                            INSERT INTO classes (
                                repo_id, file_path, name, docstring
                            )
                            VALUES (
                                (SELECT repo_id FROM code_snippets WHERE file_path = %s LIMIT 1),
                                %s, %s, %s
                            )
                            ON CONFLICT (file_path, name) DO UPDATE
                            SET docstring = EXCLUDED.docstring
                        ''', (file_path, file_path, cls['name'], cls.get('docstring')))
                
                self._conn.commit()
                
                self._log('info', 'Updated AST relationships',
                         file_path=file_path,
                         function_count=len(relationships.get('functions', [])),
                         class_count=len(relationships.get('classes', [])),
                         duration_ms=int((time.time() - start_time) * 1000))
        except Exception as e:
            self._log('error', 'Failed to update AST relationships',
                     file_path=file_path,
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            self._conn.rollback()
            raise

    def _execute_query(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Execute a query and return results."""
        start_time = time.time()
        self.ensure_connection()
        try:
            with self._conn.cursor() as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                
                self._log('debug', 'Executed query',
                         query_length=len(query),
                         result_count=len(results),
                         duration_ms=int((time.time() - start_time) * 1000))
                return results
        except Exception as e:
            self._log('error', 'Failed to execute query',
                     query_length=len(query),
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

    def get_repository_files(self, repo_id: int) -> List[Dict[str, Any]]:
        """Get all files for a given repository.
        
        Args:
            repo_id: The ID of the repository
            
        Returns:
            List of dictionaries containing file information
        """
        start_time = time.time()
        self.ensure_connection()
        try:
            with self._conn.cursor() as cur:
                cur.execute('''
                    SELECT DISTINCT file_path, language
                    FROM code_snippets
                    WHERE repo_id = %s
                    ORDER BY file_path
                ''', (repo_id,))
                columns = [desc[0] for desc in cur.description]
                files = [dict(zip(columns, row)) for row in cur.fetchall()]
                
                self._log('debug', 'Retrieved repository files',
                         repo_id=repo_id,
                         file_count=len(files),
                         duration_ms=int((time.time() - start_time) * 1000))
                return files
        except Exception as e:
            self._log('error', 'Failed to retrieve repository files',
                     repo_id=repo_id,
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

    def get_file_count(self) -> int:
        """Get the total number of unique files in the database."""
        start_time = time.time()
        self.ensure_connection()
        try:
            with self._conn.cursor() as cur:
                cur.execute('SELECT COUNT(DISTINCT file_path) FROM code_snippets')
                count = cur.fetchone()[0]
                
                self._log('debug', 'Retrieved file count',
                         count=count,
                         duration_ms=int((time.time() - start_time) * 1000))
                return count
        except Exception as e:
            self._log('error', 'Failed to get file count',
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

    def get_repository_count(self) -> int:
        """Get the total number of repositories in the database."""
        start_time = time.time()
        self.ensure_connection()
        try:
            with self._conn.cursor() as cur:
                cur.execute('SELECT COUNT(*) FROM repositories')
                count = cur.fetchone()[0]
                
                self._log('debug', 'Retrieved repository count',
                         count=count,
                         duration_ms=int((time.time() - start_time) * 1000))
                return count
        except Exception as e:
            self._log('error', 'Failed to get repository count',
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

    def get_language_distribution(self) -> Dict[str, int]:
        """Get the distribution of programming languages in the database."""
        start_time = time.time()
        self.ensure_connection()
        try:
            with self._conn.cursor() as cur:
                cur.execute('''
                    SELECT language, COUNT(*) as count
                    FROM code_snippets
                    GROUP BY language
                    ORDER BY count DESC
                ''')
                distribution = {row[0]: row[1] for row in cur.fetchall()}
                
                self._log('debug', 'Retrieved language distribution',
                         language_count=len(distribution),
                         total_snippets=sum(distribution.values()),
                         duration_ms=int((time.time() - start_time) * 1000))
                return distribution
        except Exception as e:
            self._log('error', 'Failed to get language distribution',
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

    def get_database_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the database state."""
        start_time = time.time()
        try:
            info = {
                'file_count': self.get_file_count(),
                'repository_count': self.get_repository_count(),
                'language_distribution': self.get_language_distribution(),
                'languages': list(self.get_languages())
            }
            
            self._log('info', 'Retrieved database info',
                     file_count=info['file_count'],
                     repo_count=info['repository_count'],
                     language_count=len(info['languages']),
                     duration_ms=int((time.time() - start_time) * 1000))
            return info
        except Exception as e:
            self._log('error', 'Failed to get database info',
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

    def __enter__(self):
        """Context manager entry."""
        self.ensure_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            self._log('error', 'Error in context manager',
                     error=str(exc_val))
        self.disconnect() 