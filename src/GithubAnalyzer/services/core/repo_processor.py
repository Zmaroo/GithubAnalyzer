"""Repository processor for analyzing GitHub repositories."""
from typing import List, Dict, Any, Optional
import git
import tempfile
import os
import time
import threading
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from datetime import datetime

from GithubAnalyzer.services.core.database.postgres_service import PostgresService
from GithubAnalyzer.services.core.parser_service import ParserService
from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
from GithubAnalyzer.services.core.file_service import FileService
from GithubAnalyzer.utils.logging import get_logger
from GithubAnalyzer.services.analysis.parsers.query_service import TreeSitterQueryHandler
from GithubAnalyzer.models.core.file import FileInfo, FilePattern, FileFilterConfig
from GithubAnalyzer.models.core.database import CodeSnippet, Function, File
from GithubAnalyzer.services.analysis.parsers.language_service import LanguageService
from GithubAnalyzer.services.analysis.parsers.custom_parsers import get_custom_parser
from GithubAnalyzer.services.analysis.parsers.utils import (
    get_node_text,
    node_to_dict,
    iter_children,
    get_node_hierarchy,
    find_common_ancestor
)

load_dotenv()
# Initialize logger
logger = get_logger(__name__)

@dataclass
class RepoProcessor:
    """Service for processing GitHub repositories."""
    
    def __post_init__(self):
        """Initialize the repository processor."""
        self._logger = logger
        self._start_time = time.time()
        
        self._logger.debug("Initializing repository processor", extra={
            'context': {
                'module': 'repo_processor',
                'thread': threading.get_ident(),
                'duration_ms': 0
            }
        })
        
        self.pg_service = PostgresService()
        self.neo4j_service = Neo4jService()
        self.file_service = FileService()
        self.parser_service = ParserService()
        self.language_service = LanguageService()
        self._query_handler = TreeSitterQueryHandler()
        
        self._logger.info("Repository processor initialized", extra={
            'context': {
                'module': 'repo_processor',
                'thread': threading.get_ident(),
                'duration_ms': (time.time() - self._start_time) * 1000
            }
        })
        
    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """Get standard context for logging.
        
        Args:
            **kwargs: Additional context key-value pairs
            
        Returns:
            Dict with standard context fields plus any additional fields
        """
        context = {
            'module': 'repo_processor',
            'thread': threading.get_ident(),
            'duration_ms': (time.time() - self._start_time) * 1000
        }
        context.update(kwargs)
        return context

    def _log(self, level: str, message: str, **kwargs) -> None:
        """Log with consistent context.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Message to log
            **kwargs: Additional context key-value pairs
        """
        context = self._get_context(**kwargs)
        getattr(self._logger, level)(message, extra={'context': context})
        
    def process_repo(self, repo_url: str, repo_id: int) -> bool:
        """Process a repository from its URL.
        
        Args:
            repo_url: URL of the repository to process
            repo_id: ID of the repository in the database
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        start_time = time.time()
        self._log("info", "Starting repository processing",
                 repo_url=repo_url, repo_id=repo_id)
        
        try:
            # Clone repository
            repo_path = self.file_service.clone_repository(repo_url)
            if not repo_path:
                self._log("error", "Failed to clone repository",
                         repo_url=repo_url)
                return False
                
            # Get repository files
            files = self.file_service.get_repository_files(repo_path, repo_id=repo_id)
            if not files:
                self._log("warning", "No files found in repository",
                         repo_url=repo_url,
                         repo_path=str(repo_path))
                return False
                
            # Process each file
            processed_count = 0
            skipped_count = 0
            error_count = 0
            
            for file_info in files:
                try:
                    snippet = self._process_file(file_info)
                    if snippet:
                        # Store in databases
                        self._store_in_postgres(snippet)
                        if snippet.ast_data:
                            self._store_ast_in_neo4j(snippet)
                        processed_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    error_count += 1
                    self._log("error", "Error processing file",
                             file=str(file_info.path),
                             error=str(e))
                    
            duration = (time.time() - start_time) * 1000
            self._log("info", "Repository processing completed",
                     repo_url=repo_url,
                     total_files=len(files),
                     processed=processed_count,
                     skipped=skipped_count,
                     errors=error_count,
                     duration_ms=duration)
            
            return True
            
        except Exception as e:
            self._log("error", "Repository processing failed",
                     repo_url=repo_url,
                     error=str(e))
            return False
            
    def _process_file(self, file_info: FileInfo) -> Optional[CodeSnippet]:
        """Process a single file from the repository.
        
        Returns:
            - None if the file cannot be processed (encoding errors, read errors, etc.)
            - CodeSnippet with syntax_valid=False if the file can be read but not parsed
            - CodeSnippet with syntax_valid=True if the file is successfully parsed
        """
        start_time = time.time()
        try:
            # Try to read file content first
            try:
                with open(file_info.path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (UnicodeDecodeError, IOError) as e:
                self._log("debug", "File read error",
                         file=str(file_info.path),
                         error=str(e))
                return None

            # Handle empty files
            if not content.strip():
                self._log("debug", "Empty file",
                         file=str(file_info.path))
                return None

            # Always try custom parser first for supported file types
            custom_parser = get_custom_parser(str(file_info.path))
            if custom_parser:
                ast_data = self._parse_with_custom_parser(content, file_info.path)
                if ast_data:
                    self._log("debug", "Successfully parsed with custom parser",
                             file=str(file_info.path),
                             parser_type="custom")
                    return CodeSnippet(
                        id=None,
                        repo_id=0,  # Default repo ID
                        file_path=str(file_info.path),
                        code_text=content,
                        language=file_info.language,
                        ast_data=ast_data,
                        syntax_valid=True,
                        embedding=[0.0] * 768,  # Default zero embedding
                        created_at=datetime.now()
                    )

            # Process with tree-sitter if language is supported
            if self.language_service.is_language_supported(file_info.language):
                ast_data = self._parse_with_tree_sitter(content, file_info.language)
                if ast_data:
                    duration = (time.time() - start_time) * 1000
                    self._log("debug", "File processed successfully",
                             file=str(file_info.path),
                             language=file_info.language,
                             parser_type="tree-sitter",
                             duration_ms=duration)
                    return CodeSnippet(
                        id=None,
                        repo_id=0,  # Default repo ID
                        file_path=str(file_info.path),
                        code_text=content,
                        language=file_info.language,
                        ast_data=ast_data,
                        syntax_valid=ast_data.get('syntax_valid', True),  # Default to True if not specified
                        embedding=[0.0] * 768,  # Default zero embedding
                        created_at=datetime.now()
                    )

            # If we get here, we have valid content but no successful parse
            # Return a CodeSnippet with syntax_valid=False
            self._log("debug", "No successful parse",
                     file=str(file_info.path),
                     language=file_info.language or "unknown")
            return CodeSnippet(
                id=None,
                repo_id=0,  # Default repo ID
                file_path=str(file_info.path),
                code_text=content,
                language=file_info.language or "unknown",
                ast_data={},
                syntax_valid=False,
                embedding=[0.0] * 768,  # Default zero embedding
                created_at=datetime.now()
            )

        except Exception as e:
            self._log("error", "Error processing file",
                     file=str(file_info.path),
                     error=str(e))
            return None

    def _parse_with_tree_sitter(self, content: str, language: str) -> Optional[Dict]:
        """Parse file content using tree-sitter.
        
        Args:
            content: File content to parse
            language: Programming language to use for parsing
            
        Returns:
            Dictionary containing AST data if successful, None otherwise
        """
        try:
            parse_result = self.parser_service.parse_content(content, language)
            if not parse_result or not parse_result.tree:
                self._log("error", "Failed to parse content",
                         language=language)
                return {
                    'syntax_valid': False,
                    'errors': ['Failed to parse content'],
                    'error_nodes': [],
                    'missing_nodes': []
                }
                
            # Extract AST data even if there are syntax errors
            # Tree-sitter will provide a partial AST
            ast_data = self._extract_ast_data(parse_result)
            
            # Check if the root node has any syntax errors
            syntax_valid = not parse_result.tree.root_node.has_error
            
            # Include AST data and error information
            result = ast_data or {}
            result['syntax_valid'] = syntax_valid
            result['errors'] = parse_result.errors if hasattr(parse_result, 'errors') else []
            result['error_nodes'] = [node_to_dict(node) for node in parse_result.error_nodes] if hasattr(parse_result, 'error_nodes') else []
            result['missing_nodes'] = [node_to_dict(node) for node in parse_result.missing_nodes] if hasattr(parse_result, 'missing_nodes') else []
            
            return result
            
        except Exception as e:
            self._log("error", "Tree-sitter parsing error",
                     language=language,
                     error=str(e))
            return {
                'syntax_valid': False,
                'errors': [str(e)],
                'error_nodes': [],
                'missing_nodes': []
            }
            
    def _parse_with_custom_parser(self, content: str, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse file content using a custom parser.
        
        Args:
            content: File content to parse
            file_path: Path to the file
            
        Returns:
            Parsed AST data if successful, None otherwise
        """
        try:
            parser = get_custom_parser(str(file_path))
            if parser:
                return parser.parse(content)
            return None
        except Exception as e:
            self._log("error", "Custom parser error",
                     file=str(file_path),
                     error=str(e))
            return None

    def _extract_ast_data(self, parse_result) -> Dict[str, Any]:
        """Extract AST data from parse result."""
        if not parse_result.tree or not parse_result.tree.root_node:
            return {}
            
        return node_to_dict(parse_result.tree.root_node)
        
    def _store_ast_in_neo4j(self, snippet: CodeSnippet) -> None:
        """Store AST structure in Neo4j.
        
        Args:
            snippet: CodeSnippet containing AST data
        """
        if not snippet.ast_data:
            return
            
        # Store in Neo4j
        file = File(
            path=snippet.file_path,
            repo_id=snippet.repo_id,
            language=snippet.language,
            functions=[]
        )
        self.neo4j_service.create_file_node(file)
        
        # Store functions
        for function, ast_data in snippet.ast_data.items():
            self.neo4j_service.create_function_node(function, ast_data)
            
        # Create function relationships
        for caller, caller_data in snippet.ast_data.items():
            for callee, callee_data in snippet.ast_data.items():
                if caller != callee:
                    # Check for function calls in the caller's AST data
                    if self._has_function_call(caller_data, callee):
                        self.neo4j_service.create_function_relationship(caller, callee)

    def _has_function_call(self, ast_data: Dict[str, Any], function_name: str) -> bool:
        """Check if the AST data contains a call to the given function.
        
        Args:
            ast_data: AST data to search in
            function_name: Name of the function to look for
            
        Returns:
            True if a call to the function is found, False otherwise
        """
        # If this is a call node, check if it's calling our target function
        if ast_data.get('type') == 'call':
            for child in ast_data.get('children', []):
                if (child.get('type') == 'identifier' and 
                    child.get('text') == function_name):
                    return True
                    
        # Recursively check children
        for child in ast_data.get('children', []):
            if isinstance(child, dict) and self._has_function_call(child, function_name):
                return True
                
        return False

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