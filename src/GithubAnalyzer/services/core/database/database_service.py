from typing import List, Dict, Any, Optional

from GithubAnalyzer.services.core.database.postgres_service import PostgresService
from GithubAnalyzer.utils.db_cleanup import DatabaseCleaner
from datetime import datetime
from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
from GithubAnalyzer.models.core.database import CodeSnippet, Function, File, CodebaseQuery

"""Service for coordinated database operations and AI agent interactions.

This service acts as a high-level coordinator between different components:

1. Database Layer:
   - PostgreSQL (via PostgresService): Stores code snippets and their semantic embeddings
   - Neo4j (via Neo4jService): Stores structural relationships between code elements

2. Code Analysis Layer:
   - Uses TreeSitterQueryHandler (via ParserService) for precise AST-based code analysis
   - Combines semantic search (embeddings) with structural analysis (AST)

The service provides two main types of queries:
1. Natural Language Queries (query_codebase, semantic_code_search):
   - Uses embeddings for semantic similarity
   - Returns both code snippets and their relationships

2. Structural Queries (find_similar_patterns, get_code_context):
   - Uses TreeSitter for precise AST matching
   - Analyzes code structure and relationships

This dual approach allows for both:
- High-level semantic understanding (what the code does)
- Low-level structural analysis (how the code works)
"""

class DatabaseService:
    """Service for coordinated database operations and AI agent interactions."""
    
    def __init__(self):
        self.pg_service = PostgresService()
        self.neo4j_service = Neo4jService()
        self.cleaner = DatabaseCleaner()
    
    def initialize_databases(self) -> None:
        """Initialize database schemas and constraints."""
        # Initialize PostgreSQL
        with self.pg_service as pg:
            pg.setup_vector_extension()
            pg.drop_tables()  # Drop existing tables first
            pg.create_tables()
            
        # Initialize Neo4j
        with self.neo4j_service as neo4j:
            neo4j.setup_constraints()
    
    def cleanup_databases(self) -> None:
        """Clean up all databases."""
        self.cleaner.cleanup_all()
    
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
    
    def analyze_code_structure(self, code_snippet: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Perform detailed structural analysis of code using TreeSitter.
        
        This method utilizes advanced TreeSitterQueryHandler features for precise code analysis:
        - AST-based pattern matching
        - Syntax validation
        - Missing node detection
        - Query optimization
        
        Args:
            code_snippet: Code to analyze
            language: Optional language identifier (auto-detected if not provided)
            
        Returns:
            Dictionary containing:
            - syntax_valid: Whether the code is syntactically valid
            - error_messages: List of syntax errors if any
            - functions: List of function definitions with their properties
            - classes: List of class definitions with their properties
            - relationships: Dictionary of code relationships
            - complexity_metrics: Basic complexity metrics
        """
        from GithubAnalyzer.services.core.parser_service import ParserService
        
        parser_service = ParserService()
        parse_result = parser_service.parse_content(code_snippet, language)
        
        if not parse_result.tree:
            return {
                'syntax_valid': False,
                'error_messages': ['Failed to parse code'],
                'functions': [],
                'classes': [],
                'relationships': {},
                'complexity_metrics': {}
            }
            
        # Get query handler from parser service
        query_handler = parser_service._query_handler
        
        # Validate syntax
        is_valid, errors = query_handler.validate_syntax(parse_result.tree.root_node)
        
        # Find functions and classes
        functions = query_handler.find_functions(parse_result.tree)
        classes = query_handler.find_classes(parse_result.tree.root_node)
        
        # Find relationships between nodes
        relationships = {}
        for func in functions:
            # Get function calls and references
            func_node = func.get('function.def')
            if func_node:
                calls = query_handler.find_nodes(func_node, "call")
                relationships[func.get('function.name', '')] = {
                    'calls': [call.get('function', '') for call in calls],
                    'references': []  # Add reference analysis here
                }
        
        return {
            'syntax_valid': is_valid,
            'error_messages': errors,
            'functions': [
                {
                    'name': f.get('function.name', '').text.decode('utf8'),
                    'params': f.get('function.params', '').text.decode('utf8'),
                    'body': f.get('function.body', '').text.decode('utf8')
                }
                for f in functions
            ],
            'classes': [
                {
                    'name': c.get('class.name', '').text.decode('utf8'),
                    'methods': [
                        m.get('method.name', '').text.decode('utf8')
                        for m in query_handler.find_nodes(
                            c.get('class.body', c), 'method'
                        )
                    ]
                }
                for c in classes
            ],
            'relationships': relationships,
            'complexity_metrics': {
                'function_count': len(functions),
                'class_count': len(classes),
                'total_lines': len(code_snippet.splitlines())
            }
        }
    
    def query_codebase(self, query: str, limit: int = 5) -> CodebaseQuery:
        """Query the codebase using natural language.
        
        This method combines semantic search with structural analysis:
        1. First, it finds semantically similar code using embeddings
        2. Then, it analyzes the structure of matching code using TreeSitter
        3. Finally, it combines both results for comprehensive understanding
        
        Args:
            query: Natural language query about the code
            limit: Maximum number of results to return
            
        Returns:
            CodebaseQuery containing both semantic matches and their structural relationships
        """
        with self.pg_service as pg:
            # First, find semantically similar code
            similar_code = pg.find_similar_code(query, limit=limit)
            
            # Convert to CodeSnippet objects
            snippets = []
            for file_path, code, _ in similar_code:
                # Analyze code structure using TreeSitter
                structure = self.analyze_code_structure(code)
                
                snippet = CodeSnippet(
                    id=None,  # We don't need the ID for display
                    repo_id="",  # This info might not be needed for display
                    file_path=file_path,
                    code_text=code,
                    embedding=[],  # We don't need to expose the embedding
                    created_at=datetime.now(),  # This is just for display
                    # Add structural information
                    syntax_valid=structure['syntax_valid'],
                    functions=structure['functions'],
                    classes=structure['classes'],
                    complexity=structure['complexity_metrics']
                )
                snippets.append(snippet)
            
            # For each matching file, get its structural relationships from Neo4j
            with self.neo4j_service as neo4j:
                relationships = []
                for snippet in snippets:
                    # Combine both database and AST relationships
                    db_relationships = neo4j.get_file_relationships(snippet.file_path)
                    ast_relationships = self.analyze_code_structure(
                        snippet.code_text
                    )['relationships']
                    
                    # Merge relationships from both sources
                    combined = db_relationships.copy()
                    for func, rels in ast_relationships.items():
                        if func in combined:
                            combined[func]['ast_calls'] = rels['calls']
                            combined[func]['ast_references'] = rels['references']
                        else:
                            combined[func] = {
                                'ast_calls': rels['calls'],
                                'ast_references': rels['references']
                            }
                    relationships.extend(combined.items())
                
                return CodebaseQuery(
                    semantic_matches=snippets,
                    structural_relationships=relationships
                ) 