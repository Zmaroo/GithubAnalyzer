"""Repository processor for analyzing GitHub repositories."""
from typing import List, Dict, Any, Optional
import git
import tempfile
import os
from pathlib import Path
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
logger = get_logger(__name__)

class RepoProcessor:
    """Service for processing GitHub repositories."""
    
    def __init__(self):
        """Initialize the repository processor."""
        self.pg_service = PostgresService()
        self.neo4j_service = Neo4jService()
        self.file_service = FileService()
        self.parser_service = ParserService()
        self.language_service = LanguageService()
        self._query_handler = TreeSitterQueryHandler()
        
    def process_repo(self, repo_url: str) -> bool:
        """Process a repository from its URL.
        
        Args:
            repo_url: URL of the repository to process
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Clone repository
            logger.info({
                "message": "Cloning repository",
                "context": {
                    "url": repo_url
                }
            })
            
            repo_path = self.file_service.clone_repository(repo_url)
            if not repo_path:
                logger.error({
                    "message": "Failed to clone repository",
                    "context": {
                        "url": repo_url
                    }
                })
                return False
                
            # Get repository files
            files = self.file_service.get_repository_files(repo_path)
            if not files:
                logger.warning({
                    "message": "No files found in repository",
                    "context": {
                        "url": repo_url,
                        "path": str(repo_path)
                    }
                })
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
                    logger.error({
                        "message": "Error processing file",
                        "context": {
                            "file": str(file_info.path),
                            "error": str(e)
                        }
                    })
                    
            # Log summary
            logger.info({
                "message": "Repository processing completed",
                "context": {
                    "url": repo_url,
                    "total_files": len(files),
                    "processed": processed_count,
                    "skipped": skipped_count,
                    "errors": error_count
                }
            })
            
            return True
            
        except Exception as e:
            logger.error({
                "message": "Repository processing failed",
                "context": {
                    "url": repo_url,
                    "error": str(e)
                }
            })
            return False
            
    def _process_file(self, file_info: FileInfo) -> Optional[CodeSnippet]:
        """Process a single file from the repository.
        
        Args:
            file_info: Information about the file to process
            
        Returns:
            CodeSnippet if processing was successful, None otherwise
        """
        try:
            # Skip if no language detected
            if not file_info.language:
                logger.debug({
                    "message": "Skipping file - no language detected",
                    "context": {
                        "file": str(file_info.path)
                    }
                })
                return None

            # Read file content
            with open(file_info.path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Skip empty files
            if not content.strip():
                logger.debug({
                    "message": "Skipping empty file",
                    "context": {
                        "file": str(file_info.path)
                    }
                })
                return None

            # Always try custom parser first for supported file types
            custom_parser = get_custom_parser(str(file_info.path))
            if custom_parser:
                ast_data = self._parse_with_custom_parser(content, file_info.path)
                if ast_data:
                    logger.debug({
                        "message": "Successfully parsed with custom parser",
                        "context": {
                            "file": str(file_info.path),
                            "parser_type": "custom"
                        }
                    })
                    return CodeSnippet(
                        file_path=str(file_info.path),
                        content=content,
                        language=file_info.language,
                        ast_data=ast_data,
                        syntax_valid=True
                    )
                else:
                    logger.warning({
                        "message": "Custom parser failed",
                        "context": {
                            "file": str(file_info.path)
                        }
                    })
                    # Don't return None here - try tree-sitter as fallback

            # Process with tree-sitter if language is supported
            if self.language_service.is_language_supported(file_info.language):
                ast_data = self._parse_with_tree_sitter(content, file_info.language)
                if ast_data:
                    return CodeSnippet(
                        file_path=str(file_info.path),
                        content=content,
                        language=file_info.language,
                        ast_data=ast_data,
                        syntax_valid=True
                    )
                else:
                    logger.warning({
                        "message": "Tree-sitter parsing failed",
                        "context": {
                            "file": str(file_info.path),
                            "language": file_info.language
                        }
                    })
                    return None

            # Store file without AST data if no parser was successful
            logger.debug({
                "message": "No parser available",
                "context": {
                    "file": str(file_info.path),
                    "language": file_info.language
                }
            })
            return CodeSnippet(
                file_path=str(file_info.path),
                content=content,
                language=file_info.language,
                ast_data={},
                syntax_valid=False
            )

        except UnicodeDecodeError:
            logger.debug({
                "message": "Skipping file - encoding error",
                "context": {
                    "file": str(file_info.path)
                }
            })
            return None
        except Exception as e:
            logger.error({
                "message": "Error processing file",
                "context": {
                    "file": str(file_info.path),
                    "error": str(e)
                }
            })
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
            tree = self.language_service.parse_content(content, language)
            if not tree:
                return None
                
            ast_data = self._extract_ast_data(tree)
            if not ast_data:
                return None
                
            return ast_data
            
        except Exception as e:
            logger.error({
                "message": "Tree-sitter parsing error",
                "context": {
                    "language": language,
                    "error": str(e)
                }
            })
            return None
            
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
            logger.error({
                "message": "Custom parser error",
                "context": {
                    "file": str(file_path),
                    "error": str(e)
                }
            })
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
        for caller, _ in snippet.ast_data.items():
            for callee, _ in snippet.ast_data.items():
                if caller != callee:
                    # Check if caller calls callee
                    caller_node = None
                    for node in parse_result.tree.root_node.children:
                        if node.type == 'function_definition':
                            for child in node.children:
                                if child.type == 'identifier' and get_node_text(child) == caller:
                                    caller_node = node
                                    break
                            if caller_node:
                                break
                                
                    if caller_node:
                        # Look for calls to callee
                        for node in caller_node.children:
                            if node.type == 'call' and any(
                                child.type == 'identifier' and get_node_text(child) == callee
                                for child in node.children
                            ):
                                self.neo4j_service.create_function_relationship(caller, callee)
                                break

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