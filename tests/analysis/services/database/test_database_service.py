"""Test suite for the AI agent interface (DatabaseService)."""
import logging
import sys
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass
import pytest
from tree_sitter import Parser, Language, Query

from tree_sitter_language_pack import get_binding, get_language, get_parser

from GithubAnalyzer.services.core.database.database_service import DatabaseService
from GithubAnalyzer.services.core.repo_processor import RepoProcessor
from GithubAnalyzer.services.analysis.parsers.tree_sitter_editor import TreeSitterEditor
from GithubAnalyzer.services.analysis.parsers.query_service import TreeSitterQueryHandler
from GithubAnalyzer.services.analysis.parsers.traversal_service import TreeSitterTraversal
from GithubAnalyzer.services.analysis.parsers.language_service import LanguageService
from GithubAnalyzer.utils.logging import get_logger, LoggerFactory, StructuredFormatter, TreeSitterLogHandler
from GithubAnalyzer.models.core.errors import LanguageError
from GithubAnalyzer.models.core.file import FileInfo

logger = get_logger(__name__)

@dataclass
class Point:
    row: int
    column: int

def setup_test_logging():
    """Set up logging for tests with proper tree-sitter integration."""
    # Create logger factory instance
    factory = LoggerFactory()
    
    # Configure main logger
    main_logger = factory.get_logger('test_database_service', level=logging.DEBUG)
    
    # Set up tree-sitter specific logging
    ts_logger = factory.get_tree_sitter_logger('tree_sitter', level=logging.DEBUG)
    
    # Set up parser-specific logging (available in tree-sitter 0.24.0+)
    parser_logger = factory.get_logger('tree_sitter.parser', level=logging.DEBUG)

def create_parser_with_logging(language: str):
    """Create a tree-sitter parser with logging enabled.
    
    Args:
        language: Language identifier (e.g. 'python', 'javascript')
        
    Returns:
        Tree-sitter parser with logging configured
    """
    # Get parser directly from tree-sitter-language-pack
    parser = get_parser(language)
    
    if not parser:
        raise ValueError(f"Could not get parser for {language}")
        
    return parser

def test_repository_analysis(repo_url: str = "https://github.com/Zmaroo/tree-sitter-language-pack.git"):
    """Test repository analysis and search functionality.
    
    Args:
        repo_url: URL of the GitHub repository to analyze
    """
    db_service = DatabaseService()
    repo_processor = RepoProcessor()
    
    # Initialize databases
    logger.info("Initializing databases...")
    db_service.initialize_databases()
    
    # Test repository analysis
    logger.info("Starting repository analysis...")
    logger.info(f"Analyzing repository: {repo_url}")
    repo_processor.process_repo(repo_url)
    
    # Verify database state
    with db_service.pg_service as pg:
        # Check if repository was stored
        repos = pg.get_repositories()
        assert any(repo['url'] == repo_url for repo in repos), "Repository not stored in database"
        logger.debug(f"Found repository in database: {repo_url}")
        
        # Check if code snippets were stored
        snippets = pg.get_all_code_snippets()
        assert len(snippets) > 0, "No code snippets stored"
        logger.debug(f"Found {len(snippets)} code snippets")
        
        # Check if embeddings were generated
        assert all('embedding' in snippet for snippet in snippets), "Missing embeddings"
        logger.debug("All snippets have embeddings")
    
    # Test semantic search
    logger.info("Testing semantic search...")
    search_results = db_service.semantic_code_search(
        "Find all language definitions and configurations",
        limit=5
    )
    assert len(search_results) > 0, "No search results found"
    logger.debug(f"Found {len(search_results)} semantic matches")
    
    # Test codebase querying with proper parsers
    logger.info("Testing codebase querying...")
    query_results = db_service.query_codebase(
        "How are language parsers initialized?",
        limit=5
    )
    assert len(query_results.semantic_matches) > 0, "No semantic matches found"
    assert len(query_results.structural_relationships) > 0, "No structural relationships found"
    logger.debug(f"Found {len(query_results.semantic_matches)} matches and {len(query_results.structural_relationships)} relationships")

def test_code_analysis():
    """Test code analysis functionality."""
    logger.info("Starting code analysis test...")
    db_service = DatabaseService()
    
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
    assert language == "python", "Failed to detect Python language"
    logger.debug(f"Detected language: {language}")
    
    # Create parser with logging and proper language initialization
    parser = create_parser_with_logging("python")
    
    # Test structural analysis with proper parsers
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
    logger.info("Starting code editing test...")
    db_service = DatabaseService()
    
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
    
    # Create parser with logging and proper language initialization
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
    logger.info("Starting language support test...")
    db_service = DatabaseService()
    language_service = LanguageService()
    
    # Get language support info
    logger.info("Testing language support...")
    support_info = db_service.get_language_support()
    
    # Verify core languages are supported
    core_languages = {
        'python', 'javascript', 'typescript', 'java', 'rust', 'go',
        'cpp', 'c', 'ruby', 'php'
    }
    for lang in core_languages:
        assert lang in support_info['supported_languages'], f"{lang} not supported"
    logger.debug(f"Found {len(support_info['supported_languages'])} supported languages")
    
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
        'test.php': 'php',
        'test.html': 'html',
        'test.css': 'css',
        'test.yml': 'yaml',
        'Dockerfile': 'dockerfile',
        'Makefile': 'make',
        '.gitignore': 'gitignore'
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
        ''': 'typescript',
        
        # Rust
        '''
        pub fn test() -> Result<String, Error> {
            let mut value = String::new();
            Ok(value)
        }
        ''': 'rust',
        
        # Go
        '''
        package main
        
        func test() error {
            var x string
            return nil
        }
        ''': 'go',
        
        # Java
        '''
        public class Test {
            private void example() {
                System.out.println("test");
            }
        }
        ''': 'java'
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
        test_repository_analysis(repo_url)
        test_code_analysis()
        test_code_editing()
        test_language_support()
        logger.info("All tests completed successfully!")
    except Exception as e:
        logger.exception("Test suite failed")
        raise

if __name__ == "__main__":
    main() 