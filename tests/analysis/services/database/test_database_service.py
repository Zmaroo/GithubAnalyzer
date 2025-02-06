"""Test suite for the AI agent interface (DatabaseService)."""
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pytest
from tree_sitter import Language, Parser, Query
from tree_sitter_language_pack import get_binding, get_language, get_parser

from GithubAnalyzer.models.core.errors import LanguageError
from GithubAnalyzer.models.core.file import FileInfo
from GithubAnalyzer.services.analysis.parsers.language_service import \
    LanguageService
from GithubAnalyzer.services.analysis.parsers.query_service import \
    TreeSitterQueryHandler
from GithubAnalyzer.services.analysis.parsers.traversal_service import \
    TreeSitterTraversal
from GithubAnalyzer.services.analysis.parsers.tree_sitter_editor import \
    TreeSitterEditor
from GithubAnalyzer.services.core.database.database_service import \
    DatabaseService
from GithubAnalyzer.services.core.repo_processor import RepoProcessor
from GithubAnalyzer.utils.logging import (LoggerFactory, StructuredFormatter,
                                          get_logger)

logger = get_logger(__name__)

@dataclass
class Point:
    row: int
    column: int

def setup_test_logging():
    """Set up logging for tests with structured formatting."""
    # Configure root logger
    logging.basicConfig(level=logging.DEBUG)
    
    # Create main logger
    main_logger = logging.getLogger('test_database_service')
    main_logger.setLevel(logging.DEBUG)
    
    # Create tree-sitter logger
    ts_logger = logging.getLogger('tree_sitter')
    ts_logger.setLevel(logging.DEBUG)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add handler to loggers
    main_logger.addHandler(console_handler)
    ts_logger.addHandler(console_handler)
    
    return {
        'main_logger': main_logger,
        'ts_logger': ts_logger,
        'parser_logger': ts_logger.getChild('parser')
    }

def create_parser_with_logging(language: str) -> Parser:
    """Create a tree-sitter parser with logging enabled.
    
    Args:
        language: Language identifier (e.g. 'python', 'javascript')
        
    Returns:
        Tree-sitter parser with logging configured
    """
    # Get the parser
    parser = get_parser(language)
    
    # Set up logging callback
    ts_logger = logging.getLogger('tree_sitter')
    def logger_callback(msg: str) -> None:
        ts_logger.debug(msg)
    
    # Set the logger on the parser
    parser.set_logger_callback(logger_callback)
    
    return parser

def test_repository_analysis():
    """Test repository analysis and search functionality."""
    db_service = DatabaseService()
    repo_processor = RepoProcessor()
    
    # Initialize databases
    logger.info("Initializing databases...")
    db_service.cleanup_databases()  # Clean up first
    db_service.initialize_databases()
    
    # Use sample project for testing
    test_repo_url = "file://" + str(Path(__file__).parent.parent.parent.parent / "data" / "sample_project")
    logger.info(f"Analyzing repository: {test_repo_url}")
    
    # Create repository and get its ID
    repo_id = db_service.pg_service.create_repository(
        url=test_repo_url,
        resource_type='codebase'
    )
    assert repo_id is not None, "Failed to create repository"
    
    # Process the repository
    success = repo_processor.process_repo(test_repo_url, repo_id)
    assert success, "Failed to process repository"
    
    # Verify database state
    with db_service.pg_service as pg:
        # Check if repository was stored
        repos = pg.get_repositories()
        repo_entry = next((r for r in repos if r['repo_url'] == test_repo_url), None)
        assert repo_entry is not None, "Repository not stored in database"
        assert repo_entry['id'] == repo_id, "Repository ID mismatch"
        logger.debug(f"Found repository in database: {test_repo_url}")
        
        # Check if code snippets were stored
        snippets = pg.get_all_code_snippets()
        assert len(snippets) > 0, "No code snippets stored"
        logger.debug(f"Found {len(snippets)} code snippets")
        
        # Verify we have both Python and JavaScript files
        python_snippets = [s for s in snippets if s['language'] == 'python']
        js_snippets = [s for s in snippets if s['language'] == 'javascript']
        assert len(python_snippets) > 0, "No Python code snippets found"
        assert len(js_snippets) > 0, "No JavaScript code snippets found"
        logger.debug(f"Found {len(python_snippets)} Python and {len(js_snippets)} JavaScript snippets")
        
        # Check if embeddings were generated
        assert all('embedding' in snippet for snippet in snippets), "Missing embeddings"
        logger.debug("All snippets have embeddings")
    
    # Test semantic search
    logger.info("Testing semantic search...")
    
    # Search for user-related code
    user_results = db_service.semantic_code_search(
        "Find code related to user management and caching",
        limit=5
    )
    assert len(user_results) > 0, "No user-related code found"
    assert any('User' in r['code_text'] for r in user_results), "User class not found"
    assert any('cache' in r['code_text'].lower() for r in user_results), "Caching logic not found"
    
    # Search for analytics code
    analytics_results = db_service.semantic_code_search(
        "Find code related to user analytics and patterns",
        limit=5
    )
    assert len(analytics_results) > 0, "No analytics-related code found"
    assert any('Analytics' in r['code_text'] for r in analytics_results), "Analytics class not found"
    
    # Test cross-language functionality
    logger.info("Testing cross-language analysis...")
    
    # Analyze code structure
    structure = db_service.analyze_code_structure(repo_id)
    
    # Check for Python-JavaScript interactions
    assert 'dependencies' in structure, "No dependencies found"
    assert 'communities' in structure, "No code communities found"
    
    # Verify we can detect related code across languages
    assert any(
        'user' in str(comp).lower() 
        for comp in structure['dependencies']['central_components']
    ), "User-related components not found in dependencies"
    
    logger.info("Repository analysis tests completed successfully")

def test_url_handling():
    """Test handling of both repository and non-repository URLs."""
    db_service = DatabaseService()
    
    # Initialize databases
    logger.info("Initializing databases...")
    db_service.cleanup_databases()  # Clean up first
    db_service.initialize_databases()
    
    # Test codebase URL
    repo_url = "file://" + str(Path(__file__).parent.parent.parent.parent / "data" / "sample_project")
    repo_id = db_service.pg_service.create_repository(
        url=repo_url,
        resource_type='codebase'
    )
    assert repo_id is not None, "Failed to create repository"
    
    # Test documentation URL
    doc_url = "https://test.com/docs"
    doc_id = db_service.pg_service.create_repository(
        url=doc_url,
        resource_type='documentation',
        name="Test Documentation",
        description="Test documentation resource"
    )
    assert doc_id is not None, "Failed to create documentation entry"
    
    # Verify database state
    with db_service.pg_service as pg:
        # Check repositories
        repos = pg.get_repositories()
        
        # Find repository entry
        repo_entry = next((r for r in repos if r['url'] == repo_url), None)
        assert repo_entry is not None, "Repository not stored in database"
        assert repo_entry['resource_type'] == 'codebase', "Repository should be marked as codebase"
        # Extract repo name from the last part of the path
        expected_name = Path(repo_url.replace("file://", "")).name
        assert repo_entry['name'] == expected_name, f"Repository name mismatch. Expected {expected_name}, got {repo_entry['name']}"
        
        # Find documentation entry
        doc_entry = next((r for r in repos if r['url'] == doc_url), None)
        assert doc_entry is not None, "Documentation not stored in database"
        assert doc_entry['resource_type'] == 'documentation', "Documentation should be marked as documentation"
        assert doc_entry['name'] == "Test Documentation", "Documentation name mismatch"

def test_code_analysis():
    """Test code analysis functionality."""
    # Set up logging
    loggers = setup_test_logging()
    logger = loggers['main_logger']
    ts_logger = loggers['ts_logger']
    
    logger.info("Starting code analysis test...")
    db_service = DatabaseService()
    
    # Clean up databases before test
    logger.info("Cleaning up databases...")
    db_service.cleanup_databases()
    db_service.initialize_databases()
    
    # Initialize services with proper language handling
    language_service = LanguageService()
    python_lang = language_service.get_language_object("python")
    query_handler = TreeSitterQueryHandler(language=python_lang, language_name="python")
    traversal = TreeSitterTraversal()
    
    # Sample code to analyze
    code = """
    @dataclass
    class UserService:
        db: Database
        
        async def get_user(self, user_id: int) -> Optional[User]:
            return await self.db.query_one(User, id=user_id)
            
        def process_data(self, data: Dict[str, Any]) -> None:
            return self.db.process(data)
    """
    
    # Test language detection
    language = language_service.detect_language(code)
    assert language == "python", f"Failed to detect Python language, got {language}"
    logger.debug(f"Detected language: {language}")
    
    # Create test repository using local test data directory
    test_repo_url = "file://" + str(Path(__file__).parent.parent.parent.parent / "data")
    test_repo_id = db_service.pg_service.create_repository(test_repo_url)
    test_file_path = "test_file.py"
    
    # Create file node
    db_service.neo4j_service.create_file_node(FileInfo(
        path=Path(test_file_path),
        language=language,
        repo_id=test_repo_id
    ))
    
    # Create class node
    db_service.neo4j_service.create_class_node(
        repo_id=test_repo_id,
        file_path=test_file_path,
        class_name="UserService",
        ast_data={
            "type": "class_definition",
            "start_point": {"row": 2, "column": 4},
            "end_point": {"row": 9, "column": 4}
        }
    )
    
    # Create function nodes
    get_user_func = {
        'repo_id': test_repo_id,
        'file_path': test_file_path,
        'name': "get_user"
    }
    process_data_func = {
        'repo_id': test_repo_id,
        'file_path': test_file_path,
        'name': "process_data"
    }
    
    get_user_ast = {
        "type": "function_definition",
        "start_point": {"row": 5, "column": 8},
        "end_point": {"row": 6, "column": 8}
    }
    process_data_ast = {
        "type": "function_definition",
        "start_point": {"row": 8, "column": 8},
        "end_point": {"row": 9, "column": 8}
    }
    
    db_service.neo4j_service.create_function_node(get_user_func, get_user_ast)
    db_service.neo4j_service.create_function_node(process_data_func, process_data_ast)
    
    # Create parser with logging
    parser = create_parser_with_logging("python")
    
    # Test structural analysis
    logger.info("Testing code structure analysis...")
    structure = db_service.analyze_code_structure(code)
    assert structure['syntax_valid'], "Invalid syntax"
    assert len(structure['functions']) == 2, "Expected 2 functions"
    assert len(structure['classes']) == 1, "Expected 1 class"
    logger.debug(f"Found {len(structure['functions'])} functions and {len(structure['classes'])} classes")
    
    # Test AST traversal with debug info
    tree = parser.parse(bytes(code, 'utf8'))
    logger.debug(f"AST root type: {tree.root_node.type}")
    logger.debug(f"AST root children count: {len(tree.root_node.children)}")
    
    functions = traversal.find_functions(tree.root_node)
    assert len(functions) == 2, "Failed to find all functions"
    logger.debug(f"Found {len(functions)} functions in AST")
    
    # Test query patterns with detailed logging
    class_query = "(class_definition) @class"
    query = Query(python_lang, class_query)
    logger.debug(f"Query pattern count: {query.pattern_count}")
    
    matches = query.matches(tree.root_node)
    assert len(matches) == 1, "Failed to find class definition"
    logger.debug(f"Found {len(matches)} class definitions")
    
    # Log query execution stats
    if query.did_exceed_match_limit:
        logger.warning("Query exceeded match limit")

def test_code_editing():
    """Test code editing functionality."""
    # Set up logging
    loggers = setup_test_logging()
    logger = loggers['main_logger']
    ts_logger = loggers['ts_logger']
    
    logger.info("Starting code editing test...")
    db_service = DatabaseService()
    
    # Clean up and initialize databases
    logger.info("Initializing databases...")
    db_service.cleanup_databases()
    db_service.initialize_databases()
    
    # Initialize services with proper language handling
    language_service = LanguageService()
    python_lang = language_service.get_language_object("python")
    editor = TreeSitterEditor()
    
    # Sample code to edit
    code = """
    def process_data(data):
        result = transform(data)
        return result
    """
    
    # Create test repository and file
    test_repo_url = "file://" + str(Path(__file__).parent.parent.parent.parent / "data")
    test_repo_id = db_service.pg_service.create_repository(test_repo_url)
    test_file_path = "test_file.py"
    
    # Store the code in the database
    db_service.store_code_data(
        repo_id=test_repo_id,
        file_path=test_file_path,
        code_text=code,
        language="python"
    )
    
    # Create parser with logging
    parser = create_parser_with_logging("python")
    
    # Parse code with debug info
    tree = parser.parse(bytes(code, 'utf8'))
    assert tree is not None, "Failed to parse code"
    logger.debug(f"Initial AST root type: {tree.root_node.type}")
    logger.debug("Successfully parsed initial code")
    
    # Test code editing with proper editor
    logger.info("Testing code editing...")
    edit_result = db_service.edit_code(
        code,
        edit_operations=[{
            'start_position': Point(row=1, column=4),
            'end_position': Point(row=1, column=16),
            'new_text': 'async def process_data'
        }]
    )
    
    # Verify edit result with detailed logging
    assert edit_result['is_valid'], "Invalid edit result"
    assert len(edit_result['errors']) == 0, f"Edit errors: {edit_result['errors']}"
    logger.debug("Edit operation completed successfully")
    
    # Parse and verify edited code with debug info
    edited_tree = parser.parse(bytes(edit_result['modified_code'], 'utf8'))
    assert edited_tree is not None, "Failed to parse edited code"
    logger.debug(f"Edited AST root type: {edited_tree.root_node.type}")
    
    # Check for syntax errors in edited code
    if edited_tree.root_node.has_error:
        error_nodes = [node for node in edited_tree.root_node.children if node.has_error]
        logger.error(f"Found {len(error_nodes)} syntax errors in edited code")
        for node in error_nodes:
            logger.error(f"Syntax error at {node.start_point} - {node.end_point}")
    else:
        logger.debug("Successfully parsed edited code without errors")

def test_language_support():
    """Test language support information."""
    # Set up logging
    loggers = setup_test_logging()
    logger = loggers['main_logger']
    
    logger.info("Starting language support test...")
    db_service = DatabaseService()
    
    # Clean up and initialize databases
    logger.info("Initializing databases...")
    db_service.cleanup_databases()
    db_service.initialize_databases()
    
    # Initialize language service
    language_service = LanguageService()
    
    # Get language support info
    logger.info("Testing language support...")
    support_info = db_service.get_language_support()
    
    # Verify core languages are supported
    core_languages = {
        'python', 'javascript', 'typescript', 'java', 'rust', 'go',
        'cpp', 'c', 'ruby', 'php'
    }
    
    supported_languages = set(support_info.get('supported_languages', []))
    for lang in core_languages:
        assert lang in supported_languages, f"{lang} not supported"
    logger.debug(f"Found {len(supported_languages)} supported languages")
    
    # Test file extension mappings
    extension_tests = {
        'test.py': 'python',
        'test.js': 'javascript',
        'test.ts': 'typescript',
        'test.jsx': 'javascript',
        'test.tsx': 'typescript',
        'test.cpp': 'cpp',
        'test.hpp': 'cpp',
        'test.rs': 'rust',
        'test.go': 'go',
        'test.java': 'java',
        'test.rb': 'ruby',
        'test.php': 'php'
    }
    
    for file_path, expected_lang in extension_tests.items():
        detected = language_service.get_language_for_file(file_path)
        assert detected == expected_lang, f"Expected {expected_lang} for {file_path}, got {detected}"
    
    # Test language detection from content
    content_tests = {
        # Python
        '''
        def test():
            class Example:
                def __init__(self):
                    pass
        ''': 'python',
        
        # JavaScript
        '''
        const test = () => {
            class Example {
                constructor() {}
            }
        }
        ''': 'javascript',
        
        # TypeScript
        '''
        interface Test {
            name: string;
            value: number;
        }
        ''': 'typescript'
    }
    
    for content, expected_lang in content_tests.items():
        detected = language_service.detect_language(content)
        assert detected == expected_lang, f"Expected {expected_lang} for content, got {detected}"
    
    # Test unsupported language handling
    with pytest.raises(LanguageError):
        language_service.get_language_object("nonexistent")
        
    with pytest.raises(LanguageError):
        language_service.get_binding("nonexistent")
        
    with pytest.raises(LanguageError):
        language_service.get_parser("nonexistent")
        
    # Test file info validation
    with pytest.raises(ValueError):
        FileInfo(path=Path("test.py"), language="nonexistent")
    
    # Verify language features
    if 'python' in support_info['language_features']:
        features = support_info['language_features']['python']
        required_features = {'functions', 'classes', 'imports'}
        assert all(f in features for f in required_features), "Missing required Python features"
        logger.debug(f"Python features verified: {', '.join(required_features)}")

def main():
    """Main entry point for testing the AI agent interface."""
    if len(sys.argv) != 2:
        logger.error("Repository URL not provided")
        print("Usage: python test_database_service.py <repository_url>")
        sys.exit(1)
        
    repo_url = sys.argv[1]
    setup_test_logging()
    
    logger.info("Starting DatabaseService (AI Agent Interface) Tests")
    logger.info("=" * 50)
    
    try:
        test_repository_analysis()
        test_url_handling()
        test_code_analysis()
        test_code_editing()
        test_language_support()
        logger.info("All tests completed successfully!")
    except Exception as e:
        logger.exception("Test suite failed")
        raise

if __name__ == "__main__":
    main() 