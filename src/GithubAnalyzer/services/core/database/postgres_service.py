from typing import Optional, List, Dict, Any, Tuple
import psycopg2

from GithubAnalyzer.services.core.database.embedding_service import CodeEmbeddingService
from psycopg2.extensions import connection
from GithubAnalyzer.services.core.database.db_config import get_postgres_config

class PostgresService:
    def __init__(self):
        self._conn: Optional[connection] = None
        self._config = get_postgres_config()
        self._embedding_service = CodeEmbeddingService()

    def connect(self) -> None:
        """Establish connection to PostgreSQL database."""
        if not self._conn or self._conn.closed:
            self._conn = psycopg2.connect(**self._config)

    def disconnect(self) -> None:
        """Close the database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()

    def setup_vector_extension(self) -> None:
        """Setup pgvector extension for code embeddings."""
        with self._conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS vector;')
            self._conn.commit()

    def create_tables(self) -> None:
        """Create necessary tables for code storage with vector embeddings."""
        with self._conn.cursor() as cur:
            # Code snippets table with vector embeddings
            cur.execute('''
                CREATE TABLE IF NOT EXISTS code_snippets (
                    id SERIAL PRIMARY KEY,
                    repo_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    code_text TEXT NOT NULL,
                    embedding vector(384),  -- Dimension depends on embedding model
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            self._conn.commit()

    def store_code_with_embedding(self, repo_id: str, file_path: str, code_text: str) -> None:
        """Store code snippet with its embedding vector.
        
        Args:
            repo_id: Repository identifier
            file_path: Path to the file containing the code
            code_text: The actual code snippet
        """
        embedding = self._embedding_service.get_embedding(code_text)
        
        with self._conn.cursor() as cur:
            cur.execute('''
                INSERT INTO code_snippets (repo_id, file_path, code_text, embedding)
                VALUES (%s, %s, %s, %s)
            ''', (repo_id, file_path, code_text, embedding))
            self._conn.commit()

    def find_similar_code(self, query_code: str, limit: int = 5) -> List[Tuple[str, str, float]]:
        """Find similar code snippets using vector similarity search.
        
        Args:
            query_code: Code snippet to find similar matches for
            limit: Maximum number of results to return
            
        Returns:
            List of tuples containing (file_path, code_text, similarity_score)
        """
        query_embedding = self._embedding_service.get_embedding(query_code)
        
        with self._conn.cursor() as cur:
            cur.execute('''
                SELECT file_path, code_text, 1 - (embedding <=> %s) as similarity
                FROM code_snippets
                ORDER BY embedding <=> %s
                LIMIT %s
            ''', (query_embedding, query_embedding, limit))
            
            return [(row[0], row[1], row[2]) for row in cur.fetchall()]

    def batch_store_code(self, code_entries: List[Tuple[str, str, str]]) -> None:
        """Store multiple code snippets with their embeddings in batch.
        
        Args:
            code_entries: List of tuples containing (repo_id, file_path, code_text)
        """
        code_texts = [entry[2] for entry in code_entries]
        embeddings = self._embedding_service.get_embeddings(code_texts)
        
        with self._conn.cursor() as cur:
            for (repo_id, file_path, code_text), embedding in zip(code_entries, embeddings):
                cur.execute('''
                    INSERT INTO code_snippets (repo_id, file_path, code_text, embedding)
                    VALUES (%s, %s, %s, %s)
                ''', (repo_id, file_path, code_text, embedding))
            self._conn.commit()

    def create_repository(self, repo_url: str) -> str:
        """Create a new repository entry.
        
        Args:
            repo_url: URL of the GitHub repository
            
        Returns:
            Repository ID
        """
        with self._conn.cursor() as cur:
            # Extract repo name from URL
            repo_name = repo_url.split('/')[-1]
            
            cur.execute('''
                INSERT INTO repositories (repo_url, repo_name)
                VALUES (%s, %s)
                RETURNING id
            ''', (repo_url, repo_name))
            
            repo_id = cur.fetchone()[0]
            self._conn.commit()
            return str(repo_id)

    def semantic_search(self, query: str, limit: int = 5, 
                       filter_repo: Optional[str] = None) -> List[Dict[str, Any]]:
        """Semantic search across code, docstrings, and comments.
        
        Args:
            query: Natural language query
            limit: Maximum number of results
            filter_repo: Optional repository ID to filter by
            
        Returns:
            List of relevant code snippets with context
        """
        query_embedding = self._embedding_service.get_embedding(query)
        
        with self._conn.cursor() as cur:
            # Search in code snippets
            filter_clause = "WHERE repo_id = %s" if filter_repo else ""
            cur.execute(f'''
                WITH ranked_snippets AS (
                    SELECT 
                        cs.id,
                        cs.file_path,
                        cs.content,
                        1 - (cs.content_embedding <=> %s) as similarity,
                        f.name as function_name,
                        f.docstring as function_doc,
                        c.name as class_name,
                        c.docstring as class_doc,
                        cm.content as comments
                    FROM code_snippets cs
                    LEFT JOIN functions f ON cs.id = f.code_snippet_id
                    LEFT JOIN classes c ON cs.id = c.code_snippet_id
                    LEFT JOIN comments cm ON cs.id = cm.code_snippet_id
                    {filter_clause}
                    ORDER BY cs.content_embedding <=> %s
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
                    'similarity': row[3],
                    'context': {
                        'function': {'name': row[4], 'docstring': row[5]},
                        'class': {'name': row[6], 'docstring': row[7]},
                        'comments': row[8]
                    }
                })
            
            return results

    def get_code_context(self, file_path: str, line_number: int) -> Dict[str, Any]:
        """Get comprehensive context for a code location.
        
        Args:
            file_path: Path to the file
            line_number: Line number of interest
            
        Returns:
            Dictionary with code context
        """
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
        """Get documentation context for a query.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with relevant documentation
        """
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

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect() 