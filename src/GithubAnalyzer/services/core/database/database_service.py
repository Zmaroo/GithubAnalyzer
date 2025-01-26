from typing import List, Dict, Any, Optional

from GithubAnalyzer.services.core.database.postgres_service import PostgresService
from GithubAnalyzer.utils.db_cleanup import DatabaseCleaner
from datetime import datetime
from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
from GithubAnalyzer.models.core.database import CodeSnippet, Function, File, CodebaseQuery

class DatabaseService:
    """Service for coordinated database operations and AI agent interactions."""
    
    def __init__(self):
        self.pg_service = PostgresService()
        self.neo4j_service = Neo4jService()
        self.cleaner = DatabaseCleaner()
    
    def initialize_databases(self) -> None:
        """Initialize both databases with required schemas and constraints."""
        with self.pg_service as pg:
            pg.setup_vector_extension()
            pg.create_tables()
        
        with self.neo4j_service as neo4j:
            neo4j.setup_constraints()
    
    def analyze_repository(self, repo_url: str) -> str:
        """Analyze a GitHub repository and store its data.
        
        This is the main entry point for AI agents to process new repositories.
        
        Args:
            repo_url: URL of the GitHub repository to analyze
            
        Returns:
            Repository ID for future reference
        """
        with self.pg_service as pg:
            # Store repository info
            repo_id = pg.create_repository(repo_url)
            
            # Process repository contents (implemented in repo_processor.py)
            self.process_repository(repo_id, repo_url)
            
            return repo_id
    
    def semantic_code_search(self, query: str, limit: int = 5, 
                           filter_repo: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search code semantically using natural language.
        
        This method is optimized for AI agents to find relevant code snippets.
        
        Args:
            query: Natural language query about the code
            limit: Maximum number of results
            filter_repo: Optional repository ID to search within
            
        Returns:
            List of relevant code snippets with their context
        """
        with self.pg_service as pg:
            return pg.semantic_search(query, limit, filter_repo)
    
    def get_code_context(self, file_path: str, line_number: int) -> Dict[str, Any]:
        """Get full context for a specific code location.
        
        Provides AI agents with comprehensive context about a code location.
        
        Args:
            file_path: Path to the file
            line_number: Line number of interest
            
        Returns:
            Dictionary containing:
            - surrounding_code: Code snippet around the line
            - docstrings: Relevant docstrings
            - comments: Related comments
            - functions: Containing/nearby functions
            - classes: Containing/nearby classes
        """
        with self.pg_service as pg:
            return pg.get_code_context(file_path, line_number)
    
    def find_similar_patterns(self, code_snippet: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find code patterns similar to the given snippet.
        
        Helps AI agents identify common patterns and implementations.
        
        Args:
            code_snippet: Code pattern to search for
            limit: Maximum number of results
            
        Returns:
            List of similar code patterns with their context
        """
        with self.pg_service as pg:
            return pg.find_similar_patterns(code_snippet, limit)
    
    def get_documentation_context(self, query: str) -> Dict[str, Any]:
        """Get relevant documentation context for a query.
        
        Helps AI agents understand code through documentation.
        
        Args:
            query: Natural language query about code functionality
            
        Returns:
            Dictionary containing:
            - docstrings: Relevant docstrings
            - comments: Related comments
            - examples: Code examples
        """
        with self.pg_service as pg:
            return pg.get_documentation_context(query)
    
    def store_code_data(self, repo_id: str, file_path: str, code_text: str,
                       functions_data: List[Dict[str, Any]]) -> None:
        """Store code data in both databases.
        
        Args:
            repo_id: Repository identifier
            file_path: Path to the file
            code_text: The actual code content
            functions_data: List of function data including calls
        """
        with self.pg_service as pg, self.neo4j_service as neo4j:
            # Store in PostgreSQL
            snippet = CodeSnippet(
                id=None,
                repo_id=repo_id,
                file_path=file_path,
                code_text=code_text,
                embedding=[],  # Will be generated by the service
                created_at=datetime.now()
            )
            pg.store_code_with_embedding(snippet)
            
            # Store in Neo4j
            functions = []
            for func_data in functions_data:
                func = Function(
                    name=func_data['name'],
                    file_path=file_path,
                    calls=[],  # Will be populated below
                    repo_id=repo_id
                )
                functions.append(func)
            
            file = File(
                path=file_path,
                repo_id=repo_id,
                functions=functions
            )
            
            neo4j.create_file_node(file)
            
            # Process functions and their relationships
            for func_data, func in zip(functions_data, functions):
                for called_func in func_data.get('calls', []):
                    neo4j.create_function_relationship(
                        func,
                        Function(
                            name=called_func['name'],
                            file_path=called_func['file'],
                            calls=[],
                            repo_id=repo_id
                        )
                    )
    
    def batch_store_code(self, code_entries: List[Dict[str, Any]]) -> None:
        """Batch store code data in both databases.
        
        Args:
            code_entries: List of dictionaries containing code data
        """
        with self.pg_service as pg, self.neo4j_service as neo4j:
            # Prepare data for PostgreSQL
            snippets = [
                CodeSnippet(
                    id=None,
                    repo_id=entry['repo_id'],
                    file_path=entry['file_path'],
                    code_text=entry['code_text'],
                    embedding=[],  # Will be generated by the service
                    created_at=datetime.now()
                )
                for entry in code_entries
            ]
            pg.batch_store_code(snippets)
            
            # Store in Neo4j
            for entry in code_entries:
                functions = []
                for func_data in entry.get('functions_data', []):
                    func = Function(
                        name=func_data['name'],
                        file_path=entry['file_path'],
                        calls=[],
                        repo_id=entry['repo_id']
                    )
                    functions.append((func, func_data))
                
                file = File(
                    path=entry['file_path'],
                    repo_id=entry['repo_id'],
                    functions=[f[0] for f in functions]
                )
                
                neo4j.create_file_node(file)
                
                for func, func_data in functions:
                    for called_func in func_data.get('calls', []):
                        neo4j.create_function_relationship(
                            func,
                            Function(
                                name=called_func['name'],
                                file_path=called_func['file'],
                                calls=[],
                                repo_id=entry['repo_id']
                            )
                        )
    
    def query_codebase(self, query: str, limit: int = 5) -> CodebaseQuery:
        """Query the codebase using natural language.
        
        Args:
            query: Natural language query about the code
            limit: Maximum number of results to return
            
        Returns:
            CodebaseQuery containing relevant code snippets and their relationships
        """
        with self.pg_service as pg:
            # First, find semantically similar code
            similar_code = pg.find_similar_code(query, limit=limit)
            
            # Convert to CodeSnippet objects
            snippets = [
                CodeSnippet(
                    id=None,  # We don't need the ID for display
                    repo_id="",  # This info might not be needed for display
                    file_path=file_path,
                    code_text=code,
                    embedding=[],  # We don't need to expose the embedding
                    created_at=datetime.now()  # This is just for display
                )
                for file_path, code, _ in similar_code
            ]
            
            # For each matching file, get its structural relationships from Neo4j
            with self.neo4j_service as neo4j:
                relationships = []
                for snippet in snippets:
                    file_relationships = neo4j.get_file_relationships(snippet.file_path)
                    relationships.extend(file_relationships)
                
                return CodebaseQuery(
                    snippets=snippets,
                    relationships=relationships
                ) 