from typing import Optional, List, Dict, Any, Tuple, Set
import psycopg2
import json
from datetime import datetime
from psycopg2.extras import execute_values
import numpy as np
import time
import threading
from dataclasses import dataclass

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

    def create_repository(self, repo_url: str) -> int:
        """Create a new repository entry and return its ID."""
        start_time = time.time()
        self.ensure_connection()
        try:
            repo_name = repo_url.split('/')[-1]
            with self._conn.cursor() as cur:
                # Check if repo already exists
                cur.execute('SELECT id FROM repositories WHERE repo_url = %s', (repo_url,))
                existing = cur.fetchone()
                
                if existing:
                    self._log('debug', 'Repository already exists',
                             repo_url=repo_url,
                             repo_id=existing[0],
                             duration_ms=int((time.time() - start_time) * 1000))
                    return existing[0]
                
                # Create new repo
                cur.execute('''
                    INSERT INTO repositories (repo_url, repo_name)
                    VALUES (%s, %s)
                    RETURNING id
                ''', (repo_url, repo_name))
                repo_id = cur.fetchone()[0]
                self._conn.commit()
                
                self._log('info', 'Created new repository',
                         repo_url=repo_url,
                         repo_id=repo_id,
                         duration_ms=int((time.time() - start_time) * 1000))
                return repo_id
        except Exception as e:
            self._log('error', 'Failed to create repository',
                     repo_url=repo_url,
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            self._conn.rollback()
            raise

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

    def get_all_code_snippets(self) -> List[Dict[str, Any]]:
        """Get all code snippets from the database."""
        start_time = time.time()
        self.ensure_connection()
        try:
            with self._conn.cursor() as cur:
                cur.execute('''
                    SELECT cs.file_path, cs.code_text, cs.language, cs.metadata, r.repo_url
                    FROM code_snippets cs
                    JOIN repositories r ON cs.repo_id = r.id
                    WHERE cs.is_supported = true
                ''')
                results = cur.fetchall()
                
                self._log('debug', 'Retrieved all code snippets',
                         snippet_count=len(results),
                         duration_ms=int((time.time() - start_time) * 1000))
                
                return [
                    {
                        'file_path': r[0],
                        'code_text': r[1],
                        'language': r[2],
                        'metadata': r[3],
                        'repo_url': r[4]
                    }
                    for r in results
                ]
        except Exception as e:
            self._log('error', 'Failed to retrieve code snippets',
                     error=str(e),
                     duration_ms=int((time.time() - start_time) * 1000))
            raise

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