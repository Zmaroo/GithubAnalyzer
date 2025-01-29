from typing import List, Dict, Any, Optional

from GithubAnalyzer.services.core.database.postgres_service import PostgresService
from GithubAnalyzer.utils.db_cleanup import DatabaseCleaner
from datetime import datetime
from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
from GithubAnalyzer.models.core.database import CodeSnippet, Function, File, CodebaseQuery
from GithubAnalyzer.services.core.parser_service import ParserService
from GithubAnalyzer.services.analysis.parsers.query_service import TreeSitterQueryHandler
from GithubAnalyzer.services.analysis.parsers.tree_sitter_editor import TreeSitterEditor
from GithubAnalyzer.services.analysis.parsers.traversal_service import TreeSitterTraversal
from GithubAnalyzer.services.analysis.parsers.language_service import LanguageService
from GithubAnalyzer.models.core.errors import ParserError
from GithubAnalyzer.services.analysis.parsers.utils import (
    get_node_text,
    node_to_dict,
    iter_children,
    get_node_hierarchy,
    find_common_ancestor
)
from GithubAnalyzer.services.analysis.parsers.query_patterns import QUERY_PATTERNS
from GithubAnalyzer.utils.logging import get_logger
from GithubAnalyzer.services.core.repo_processor import RepoProcessor

logger = get_logger(__name__)

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
        self._query_handler = TreeSitterQueryHandler()
        self._editor = TreeSitterEditor()
        self._traversal = TreeSitterTraversal()
        self._language_service = LanguageService()
        self._parser_service = ParserService()
        self._repo_processor = RepoProcessor()
    
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
            
        # Ensure initial sync
        self.sync_databases()
    
    def sync_databases(self) -> None:
        """Synchronize data between PostgreSQL and Neo4j databases.
        
        This method ensures consistency between the two databases by:
        1. Synchronizing language information
        2. Ensuring file nodes exist for all code snippets
        3. Updating AST relationships
        4. Cleaning up orphaned nodes
        """
        # 1. Sync languages
        postgres_languages = self.pg_service.get_languages()
        self.neo4j_service.sync_language_nodes(postgres_languages)
        
        # 2. Sync code snippets with file nodes
        code_snippets = self.pg_service.get_all_code_snippets()
        for snippet in code_snippets:
            file_path = snippet['file_path']
            language = snippet['language']
            ast_data = snippet['ast_data']
            
            # Update language in Neo4j if needed
            self.neo4j_service.update_file_language(file_path, language)
            
            # Update AST relationships if valid
            if snippet['syntax_valid'] and ast_data:
                self.update_ast_relationships(file_path, ast_data)
                
        # 3. Sync relationships from Neo4j back to PostgreSQL
        neo4j_relationships = self.neo4j_service.get_all_relationships()
        for rel_data in neo4j_relationships:
            file_path = rel_data['file_path']
            relationships = rel_data['relationships']
            self.pg_service.update_ast_relationships(file_path, relationships)
            
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
                       language: Optional[str] = None) -> None:
        """Store code data with full AST information.
        
        Args:
            repo_id: Repository identifier
            file_path: Path to the file
            code_text: The actual code content
            language: Optional language identifier
        """
        # Parse code to get AST
        parse_result = self._parser_service.parse_content(code_text, language)
        if not parse_result.tree:
            return
            
        # Ensure we have a valid language
        detected_language = parse_result.language or self._language_service.detect_language(code_text)
        if not detected_language:
            # Default to 'text' for files without a specific language
            detected_language = 'text'
            
        with self.pg_service as pg, self.neo4j_service as neo4j:
            # Store code in PostgreSQL with embeddings
            snippet = CodeSnippet(
                id=None,
                repo_id=repo_id,
                file_path=file_path,
                code_text=code_text,
                embedding=[],  # Will be generated by the service
                created_at=datetime.now(),
                language=detected_language,
                ast_data=self._extract_ast_data(parse_result)
            )
            pg.store_code_with_embedding(snippet)
            
            # Store structural information in Neo4j
            self._store_ast_in_neo4j(repo_id, file_path, parse_result)
            
    def _extract_ast_data(self, parse_result) -> Dict[str, Any]:
        """Extract detailed AST data from parse result."""
        query_methods = self._language_service.get_query_methods(parse_result.language)
        ast_data = {
            'syntax_valid': parse_result.is_supported,
            'errors': parse_result.errors,
            'language': parse_result.language,
            'elements': {}
        }
        
        # Extract all supported code elements
        for method_name, query_method in query_methods.items():
            if method_name.startswith('find_'):
                element_type = method_name[5:-1]  # Remove 'find_' and 's'
                elements = query_method(parse_result.tree.root_node)
                ast_data['elements'][element_type] = [
                    {
                        'type': element_type,
                        'name': self._get_node_text(captures.get(f'{element_type}.name')),
                        'start_point': captures.get(f'{element_type}.def').start_point,
                        'end_point': captures.get(f'{element_type}.def').end_point,
                        'text': self._get_node_text(captures.get(f'{element_type}.def'))
                    }
                    for captures in elements
                    if captures.get(f'{element_type}.def')
                ]
                
        return ast_data
        
    def _store_ast_in_neo4j(self, repo_id: str, file_path: str, parse_result) -> None:
        """Store AST structure in Neo4j."""
        # Create file node
        file = File(path=file_path, repo_id=repo_id, functions=[])
        self.neo4j_service.create_file_node(file)
        
        # Extract and store code elements with relationships
        ast_data = self._extract_ast_data(parse_result)
        
        # Store functions with their relationships
        for func_data in ast_data['elements'].get('function', []):
            function = Function(
                name=func_data['name'],
                file_path=file_path,
                calls=[],
                repo_id=repo_id
            )
            
            # Find function calls within this function
            calls = self._query_handler.find_nodes(
                parse_result.tree,
                "call",
                parse_result.language
            )
            
            # Create relationships for each call
            for call in calls:
                if 'call.name' in call:
                    called_func = Function(
                        name=self._get_node_text(call['call.name']),
                        file_path=file_path,
                        calls=[],
                        repo_id=repo_id
                    )
                    self.neo4j_service.create_function_relationship(function, called_func)
                    
        # Store class hierarchies
        for class_data in ast_data['elements'].get('class', []):
            self.neo4j_service.create_class_node(
                repo_id,
                file_path,
                class_data['name'],
                {
                    'start_point': class_data['start_point'],
                    'end_point': class_data['end_point']
                }
            )
            
    def _get_node_text(self, node) -> str:
        """Safely get text from a tree-sitter node."""
        if node is None:
            return ""
        try:
            return node.text.decode('utf8')
        except (AttributeError, UnicodeDecodeError):
            return str(node)
    
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
            for result in similar_code:
                # Analyze code structure using TreeSitter
                structure = self.analyze_code_structure(result['code_text'])
                
                snippet = CodeSnippet(
                    id=None,  # We don't need the ID for display
                    repo_id="",  # This info might not be needed for display
                    file_path=result['file_path'],
                    code_text=result['code_text'],
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
    
    def edit_code(self, code: str, edit_operations: List[Dict[str, Any]], language: Optional[str] = None) -> Dict[str, Any]:
        """Edit code using tree-sitter.
        
        This method allows the AI agent to make precise edits to code while maintaining syntax validity.
        
        Args:
            code: The code to edit
            edit_operations: List of edit operations, each containing:
                - start_position: Dict with row and column
                - end_position: Dict with row and column
                - new_text: The new text to insert
            language: Optional language identifier
            
        Returns:
            Dictionary containing:
            - modified_code: The edited code
            - is_valid: Whether the resulting code is syntactically valid
            - errors: List of any syntax errors
        """
        try:
            tree = self._editor.parse_code(code)
            
            for op in edit_operations:
                edit = self._editor.create_edit_operation(
                    tree,
                    start_position=op['start_position'],
                    end_position=op['end_position'],
                    new_text=op['new_text']
                )
                self._editor.apply_edit(tree, edit)
            
            # Verify the edited code
            is_valid = self._editor.verify_tree_changes(tree)
            errors = []
            if not is_valid:
                _, errors = self._query_handler.validate_syntax(tree.root_node, language)
            
            return {
                'modified_code': tree.root_node.text.decode('utf8'),
                'is_valid': is_valid,
                'errors': errors
            }
        except Exception as e:
            raise ParserError(f"Failed to edit code: {str(e)}")

    def find_code_elements(self, code: str, element_types: List[str], language: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Find specific code elements using tree-sitter queries.
        
        This method allows the AI agent to find specific code elements like functions, classes, etc.
        
        Args:
            code: The code to analyze
            element_types: List of element types to find (e.g., ["function", "class", "decorator"])
            language: Optional language identifier
            
        Returns:
            Dictionary mapping element types to lists of found elements
        """
        try:
            tree = self._editor.parse_code(code)
            results = {}
            
            query_methods = self._language_service.get_query_methods(language or 'python')
            
            for element_type in element_types:
                if f'find_{element_type}s' in query_methods:
                    results[element_type] = query_methods[f'find_{element_type}s'](tree.root_node)
                else:
                    # Fallback to generic node finding
                    results[element_type] = self._query_handler.find_nodes(tree, element_type)
            
            return results
        except Exception as e:
            raise ParserError(f"Failed to find code elements: {str(e)}")

    def analyze_code_flow(self, code: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Analyze code control flow using tree traversal.
        
        This method helps the AI agent understand code structure and flow.
        
        Args:
            code: The code to analyze
            language: Optional language identifier
            
        Returns:
            Dictionary containing:
            - nodes: List of nodes in traversal order
            - error_nodes: List of syntax error nodes
            - missing_nodes: List of missing nodes
            - control_flow: Control flow information
        """
        try:
            tree = self._editor.parse_code(code)
            
            # Get all nodes in traversal order
            nodes = list(self._traversal.walk_tree(tree.root_node))
            
            # Find error and missing nodes
            error_nodes = self._traversal.find_error_nodes(tree.root_node)
            missing_nodes = self._traversal.find_missing_nodes(tree.root_node)
            
            # Analyze control flow
            control_flow = {
                'conditionals': self._query_handler.find_nodes(tree, "if_statement"),
                'loops': self._query_handler.find_nodes(tree, "for_statement") + 
                        self._query_handler.find_nodes(tree, "while_statement"),
                'returns': self._query_handler.find_nodes(tree, "return_statement"),
                'raises': self._query_handler.find_nodes(tree, "raise_statement")
            }
            
            return {
                'nodes': [{'type': n.type, 'text': n.text.decode('utf8')} for n in nodes],
                'error_nodes': [{'type': n.type, 'position': n.start_point} for n in error_nodes],
                'missing_nodes': [{'type': n.type, 'position': n.start_point} for n in missing_nodes],
                'control_flow': {k: [{'position': n.start_point, 'text': n.text.decode('utf8')} 
                                   for n in v] for k, v in control_flow.items()}
            }
        except Exception as e:
            raise ParserError(f"Failed to analyze code flow: {str(e)}")

    def get_language_support(self) -> Dict[str, Any]:
        """Get information about supported languages and their capabilities.
        
        This method helps the AI agent understand what languages and features are available.
        
        Returns:
            Dictionary containing:
            - supported_languages: Set of supported languages
            - language_features: Dictionary mapping languages to their supported features
            - file_extensions: Dictionary mapping file extensions to languages
        """
        return {
            'supported_languages': self._language_service.supported_languages,
            'language_features': {
                lang: list(QUERY_PATTERNS[lang].keys())
                for lang in self._language_service.supported_languages
                if lang in QUERY_PATTERNS
            },
            'file_extensions': self._language_service.extension_to_language
        }

    def delete_code_data(self, repo_id: str, file_path: str) -> None:
        """Delete code data from both databases atomically."""
        with self.pg_service as pg, self.neo4j_service as neo4j:
            # First, delete from PostgreSQL
            pg.delete_code_snippet(repo_id, file_path)
            
            # Then, delete corresponding nodes from Neo4j
            neo4j.delete_file_nodes(repo_id, file_path)
            
    def update_code_data(self, repo_id: str, file_path: str, code_text: str,
                        language: Optional[str] = None) -> None:
        """Update code data in both databases atomically."""
        # First, parse the new code
        parse_result = self._parser_service.parse_content(code_text, language)
        if not parse_result.tree:
            return
            
        with self.pg_service as pg, self.neo4j_service as neo4j:
            # Update PostgreSQL
            ast_data = self._extract_ast_data(parse_result)
            pg.update_code_snippet(
                repo_id=repo_id,
                file_path=file_path,
                code_text=code_text,
                language=parse_result.language,
                ast_data=ast_data
            )
            
            # Update Neo4j
            # First, delete old nodes
            neo4j.delete_file_nodes(repo_id, file_path)
            
            # Then create new nodes with updated data
            file = File(
                path=file_path,
                repo_id=repo_id,
                language=parse_result.language,
                functions=[]
            )
            self._store_ast_in_neo4j(repo_id, file_path, parse_result)

    def delete_file(self, repo_id: str, file_path: str) -> None:
        """Delete all data related to a file from both databases.
        
        Args:
            repo_id: Repository identifier
            file_path: Path to the file
        """
        # Delete from PostgreSQL
        self.pg_service.delete_file_snippets(file_path)
        
        # Delete from Neo4j
        self.neo4j_service.delete_file_nodes(repo_id, file_path)
        
    def update_file_language(self, file_path: str, language: str) -> None:
        """Update the language of a file in both databases.
        
        Args:
            file_path: Path to the file
            language: New language identifier
        """
        # Update in PostgreSQL
        self.pg_service.update_file_language(file_path, language)
        
        # Update in Neo4j
        self.neo4j_service.update_file_language(file_path, language)

    def update_ast_relationships(self, file_path: str, ast_data: Dict[str, Any]) -> None:
        """Update AST relationships in both databases."""
        with self.pg_service as pg, self.neo4j_service as neo4j:
            # Update PostgreSQL
            pg.update_ast_relationships(file_path, ast_data['relationships'])
            
            # Update Neo4j
            # First, delete old nodes
            neo4j.delete_file_nodes(file_path)
            
            # Then create new nodes with updated data
            file = File(
                path=file_path,
                repo_id="",  # This is a placeholder, as the repo_id is not provided in the update
                language=ast_data['language'],
                functions=[]
            )
            self._store_ast_in_neo4j(file_path, file_path, ast_data)

    def analyze_code_structure(self, repo_id: str) -> Dict[str, Any]:
        """Analyze code structure using advanced graph algorithms.
        
        This method combines multiple graph analytics approaches:
        1. Dependency Analysis (PageRank, Betweenness)
        2. Code Pattern Similarity
        3. Community Detection
        4. Path Analysis
        
        Args:
            repo_id: Repository identifier
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        analysis_results = {}
        
        # 1. Analyze dependencies
        analysis_results['dependencies'] = self.neo4j_service.analyze_code_dependencies(repo_id)
        
        # 2. Find similar patterns across the codebase
        with self.pg_service as pg:
            files = pg.get_repository_files(repo_id)
            similar_patterns = {}
            for file_path in files:
                patterns = self.neo4j_service.find_similar_code_patterns(file_path)
                if patterns:
                    similar_patterns[file_path] = patterns
            analysis_results['similar_patterns'] = similar_patterns
        
        # 3. Detect code communities
        analysis_results['communities'] = self.neo4j_service.detect_code_communities(repo_id)
        
        # 4. Analyze critical paths
        critical_functions = analysis_results['dependencies']['central_components']
        paths = []
        if len(critical_functions) >= 2:
            for i in range(len(critical_functions) - 1):
                start_func = critical_functions[i]['name']
                end_func = critical_functions[i + 1]['name']
                paths.extend(
                    self.neo4j_service.find_code_paths(start_func, end_func, repo_id)
                )
        analysis_results['critical_paths'] = paths
        
        return analysis_results
        
    def export_codebase_graph(self, repo_id: str, format: str = 'json') -> str:
        """Export the codebase graph data.
        
        Args:
            repo_id: Repository identifier
            format: Export format ('json' or 'cypher')
            
        Returns:
            Exported graph data as string
        """
        return self.neo4j_service.export_graph_data(repo_id, format)
        
    def import_codebase_graph(self, data: str, format: str = 'json') -> None:
        """Import codebase graph data.
        
        Args:
            data: Graph data to import
            format: Import format ('json' or 'cypher')
        """
        self.neo4j_service.import_graph_data(data, format)
        
    def get_code_metrics(self, repo_id: str) -> Dict[str, Any]:
        """Get comprehensive code metrics using graph analytics.
        
        This method combines various metrics:
        1. Complexity metrics from AST analysis
        2. Centrality metrics from graph analysis
        3. Community metrics from clustering
        
        Args:
            repo_id: Repository identifier
            
        Returns:
            Dictionary containing various code metrics
        """
        # Get dependency analysis
        deps = self.neo4j_service.analyze_code_dependencies(repo_id)
        
        # Get community analysis
        communities = self.neo4j_service.detect_code_communities(repo_id)
        
        # Calculate metrics
        metrics = {
            'complexity': {
                'central_components': len(deps['central_components']),
                'critical_paths': len(deps['critical_paths']),
                'communities': len(communities),
                'avg_community_size': sum(len(c) for c in communities.values()) / len(communities) if communities else 0
            },
            'centrality': {
                'top_components': [
                    {
                        'name': comp['name'],
                        'type': comp['type'],
                        'centrality_score': comp['score']
                    }
                    for comp in deps['central_components'][:5]
                ]
            },
            'modularity': {
                'community_sizes': [len(c) for c in communities.values()],
                'isolated_components': sum(1 for c in communities.values() if len(c) == 1)
            }
        }
        
        return metrics

    def process_repository(self, repo_id: int, repo_url: str) -> None:
        """Process repository contents using RepoProcessor.
        
        Args:
            repo_id: Repository identifier
            repo_url: URL of the GitHub repository
        """
        try:
            self._repo_processor.process_repo(repo_url, repo_id)
        except Exception as e:
            logger.error(f"Failed to process repository {repo_url}: {str(e)}")
            raise

    def get_stored_data(self, repo_id: Optional[int] = None) -> Dict[str, Any]:
        """Get overview of stored data.
        
        Args:
            repo_id: Optional repository ID to filter results
            
        Returns:
            Dictionary containing:
            - file_count: Number of files stored
            - language_breakdown: Count of files per language
            - functions: List of stored functions
            - classes: List of stored classes
            - relationships: Count of different relationship types
        """
        overview = {
            'postgres_data': {},
            'neo4j_data': {}
        }
        
        # Get PostgreSQL data
        with self.pg_service as pg:
            # Get file statistics
            overview['postgres_data']['file_count'] = pg.get_file_count(repo_id)
            overview['postgres_data']['language_breakdown'] = pg.get_language_statistics(repo_id)
            overview['postgres_data']['recent_files'] = pg.get_recent_files(limit=5, repo_id=repo_id)
            
        # Get Neo4j data
        with self.neo4j_service as neo4j:
            # Get graph statistics
            graph_stats = neo4j.get_graph_statistics(repo_id)
            overview['neo4j_data'] = {
                'node_counts': {
                    'files': graph_stats.get('file_count', 0),
                    'functions': graph_stats.get('function_count', 0),
                    'classes': graph_stats.get('class_count', 0)
                },
                'relationship_counts': {
                    'calls': graph_stats.get('calls_count', 0),
                    'contains': graph_stats.get('contains_count', 0),
                    'imports': graph_stats.get('imports_count', 0)
                }
            }
            
        return overview 