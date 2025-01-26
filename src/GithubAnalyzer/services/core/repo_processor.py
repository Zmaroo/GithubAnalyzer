from typing import List, Dict, Any, Optional
import git
import tempfile

from GithubAnalyzer.services.core.database.postgres_service import PostgresService
from GithubAnalyzer.services.core.parser_service import ParserService
import os
from pathlib import Path
from dotenv import load_dotenv
from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
from GithubAnalyzer.services.core.file_service import FileService
from GithubAnalyzer.utils.logging.logging_config import get_logger

load_dotenv()

class RepoProcessor:
    def __init__(self):
        self.parser_service = ParserService()
        self.file_service = FileService()
        self.pg_service = PostgresService()
        self.neo4j_service = Neo4jService()
        self.github_token = os.getenv('GITHUB_TOKEN')
        
    def clone_repo(self, repo_url: str, target_dir: str) -> str:
        """Clone a GitHub repository to a local directory.
        
        Args:
            repo_url: GitHub repository URL
            target_dir: Directory to clone into
            
        Returns:
            Path to the cloned repository
        """
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_path = os.path.join(target_dir, repo_name)
        
        if not os.path.exists(repo_path):
            if self.github_token and 'github.com' in repo_url:
                # Add token to URL for private repos
                auth_url = repo_url.replace('https://', f'https://{self.github_token}@')
                git.Repo.clone_from(auth_url, repo_path)
            else:
                git.Repo.clone_from(repo_url, repo_path)
            
        return repo_path
        
    def process_repo(self, repo_url: str) -> None:
        """Process a GitHub repository and store its data in databases.
        
        Args:
            repo_url: GitHub repository URL
        """
        # Create temporary directory for cloning
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone repository
            repo_path = self.clone_repo(repo_url, temp_dir)
            repo_id = repo_url.split('/')[-1].replace('.git', '')
            
            # Initialize database connections
            with self.pg_service as pg, self.neo4j_service as neo4j:
                # Process Python files
                python_files = list(Path(repo_path).rglob("*.py"))
                
                # Batch process for PostgreSQL
                code_entries = []
                
                for file_path in python_files:
                    relative_path = str(file_path.relative_to(repo_path))
                    
                    # Parse file
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    # Parse code structure
                    parsed_data = self.parser_service.parse_python_file(content)
                    
                    # Store in PostgreSQL
                    code_entries.append((repo_id, relative_path, content))
                    
                    # Store in Neo4j
                    neo4j.create_file_node(repo_id, relative_path)
                    
                    # Process functions and their relationships
                    for func_data in parsed_data.get('functions', []):
                        func_name = func_data['name']
                        # Store function calls in Neo4j
                        for called_func in func_data.get('calls', []):
                            neo4j.create_function_relationship(
                                relative_path, called_func['file'],
                                func_name, called_func['name']
                            )
                
                # Batch store code with embeddings in PostgreSQL
                pg.batch_store_code(code_entries)
    
    def query_codebase(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Query the codebase using natural language.
        
        Args:
            query: Natural language query about the code
            limit: Maximum number of results to return
            
        Returns:
            Dictionary containing relevant code snippets and their relationships
        """
        results = {}
        
        with self.pg_service as pg:
            # First, find semantically similar code
            similar_code = pg.find_similar_code(query, limit=limit)
            results['semantic_matches'] = similar_code
            
            # For each matching file, get its structural relationships from Neo4j
            with self.neo4j_service as neo4j:
                relationships = []
                for file_path, _, _ in similar_code:
                    # Get function relationships for this file
                    file_rels = neo4j.get_file_relationships(file_path)
                    relationships.append({
                        'file': file_path,
                        'relationships': file_rels
                    })
                
                results['structural_relationships'] = relationships
        
        return results 