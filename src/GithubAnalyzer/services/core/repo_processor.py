"""Repository processor for analyzing GitHub repositories."""
from typing import List, Dict, Any, Optional
import git
import tempfile
import os
from pathlib import Path
from dotenv import load_dotenv

from GithubAnalyzer.services.core.database.postgres_service import PostgresService
from GithubAnalyzer.services.core.parser_service import ParserService
from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
from GithubAnalyzer.services.core.file_service import FileService
from GithubAnalyzer.utils.logging import get_logger
from GithubAnalyzer.services.analysis.parsers.tree_sitter_query import TreeSitterQueryHandler

load_dotenv()
logger = get_logger(__name__)

class RepoProcessor:
    def __init__(self):
        self.parser_service = ParserService()
        self.file_service = FileService()
        self.pg_service = PostgresService()
        self.neo4j_service = Neo4jService()
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.query_handler = TreeSitterQueryHandler()
        
    def clone_repo(self, repo_url: str, target_dir: str) -> str:
        """Clone a GitHub repository to a local directory."""
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_path = os.path.join(target_dir, repo_name)
        
        if not os.path.exists(repo_path):
            if self.github_token and 'github.com' in repo_url:
                auth_url = repo_url.replace('https://', f'https://{self.github_token}@')
                git.Repo.clone_from(auth_url, repo_path)
            else:
                git.Repo.clone_from(repo_url, repo_path)
            
        return repo_path
        
    def process_repo(self, repo_url: str) -> None:
        """Process a GitHub repository and store its data in databases."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone repository
            repo_path = self.clone_repo(repo_url, temp_dir)
            
            # Initialize database connections
            with self.pg_service as pg, self.neo4j_service as neo4j:
                # Create repository entry and get ID
                repo_id = pg.create_repository(repo_url)
                
                # Process all supported files
                code_entries = []
                file_functions = {}
                
                for file_path in Path(repo_path).rglob("*"):
                    try:
                        # Skip non-file items and hidden files
                        if not file_path.is_file() or file_path.name.startswith('.'):
                            continue
                            
                        relative_path = str(file_path.relative_to(repo_path))
                        
                        # Parse file
                        parse_result = self.parser_service.parse_file(file_path)
                        if not parse_result.tree:
                            continue
                            
                        # Store code in PostgreSQL
                        with open(file_path, 'r') as f:
                            content = f.read()
                        code_entries.append((repo_id, relative_path, content))
                        
                        # Create file node in Neo4j
                        neo4j.create_file_node(repo_id, relative_path)
                        
                        # Store functions and their relationships
                        file_functions[relative_path] = {
                            'functions': parse_result.functions,
                            'classes': parse_result.classes,
                            'imports': parse_result.imports
                        }
                        
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {str(e)}")
                        continue
                
                # Create relationships in Neo4j
                self._create_relationships(repo_id, file_functions, neo4j)
                
                # Batch store code with embeddings
                pg.batch_store_code(code_entries)
                
    def _create_relationships(self, repo_id: int, file_functions: Dict[str, Dict], neo4j: Neo4jService):
        """Create relationships between code elements in Neo4j.
        
        Args:
            repo_id: Repository identifier (integer)
            file_functions: Dictionary mapping file paths to their function data
            neo4j: Neo4j service instance
        """
        # Process functions and their calls
        for file_path, data in file_functions.items():
            for func in data['functions']:
                if 'function.name' not in func:
                    continue
                    
                func_name = func['function.name'].text.decode('utf8')
                
                # Create function node
                neo4j.create_function_node(
                    repo_id=repo_id,
                    file_path=file_path,
                    name=func_name
                )
                
                # Process function body for calls
                if 'function.body' in func:
                    body_node = func['function.body']
                    calls = self.query_handler.find_nodes(body_node, "call")
                    
                    for call in calls:
                        if 'call.name' in call:
                            called_name = call['call.name'].text.decode('utf8')
                            neo4j.create_function_relationship(
                                file_path, file_path,  # We'll resolve actual file later
                                func_name, called_name
                            )
            
            # Process classes and their methods
            for cls in data['classes']:
                if 'class.name' not in cls:
                    continue
                    
                class_name = cls['class.name'].text.decode('utf8')
                
                # Create class node
                neo4j.create_class_node(
                    repo_id=repo_id,
                    file_path=file_path,
                    name=class_name
                )
                
                # Process class body for methods
                if 'class.body' in cls:
                    body_node = cls['class.body']
                    methods = self.query_handler.find_nodes(body_node, "method")
                    
                    for method in methods:
                        if 'method.name' in method:
                            method_name = method['method.name'].text.decode('utf8')
                            neo4j.create_method_relationship(
                                class_name=class_name,
                                method_name=method_name,
                                file_path=file_path
                            )
            
            # Process imports
            for imp in data['imports']:
                if 'import.module' in imp:
                    module_name = imp['import.module'].text.decode('utf8')
                    neo4j.create_import_relationship(
                        repo_id=repo_id,
                        file_path=file_path,
                        module_name=module_name
                    )
                    
    def query_codebase(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Query the codebase using natural language."""
        results = {}
        
        with self.pg_service as pg:
            # Find semantically similar code
            similar_code = pg.find_similar_code(query, limit=limit)
            results['semantic_matches'] = similar_code
            
            # Get structural relationships
            with self.neo4j_service as neo4j:
                relationships = []
                for file_path, _, _ in similar_code:
                    # Get all relationships for this file
                    file_rels = {
                        'functions': neo4j.get_function_relationships(file_path),
                        'classes': neo4j.get_class_relationships(file_path),
                        'imports': neo4j.get_import_relationships(file_path)
                    }
                    relationships.append({
                        'file': file_path,
                        'relationships': file_rels
                    })
                    
                results['structural_relationships'] = relationships
                
        return results 