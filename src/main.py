import argparse
import sys
import os
import re
import logging
import importlib.util
from pathlib import Path
from typing import Optional

def fix_imports_bootstrap():
    """Bootstrap function to fix imports without requiring package imports."""
    try:
        # Get absolute path to project root and source
        project_root = Path(__file__).resolve().parent.parent
        src_path = project_root / "src"
        
        # Add project root to Python path if not already there
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            
        # Add src to Python path if not already there
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
            
        # Import the import fixer module using importlib
        import_fixer_path = src_path / "GithubAnalyzer/utils/import_fixer.py"
        spec = importlib.util.spec_from_file_location("import_fixer", import_fixer_path)
        import_fixer = importlib.util.module_from_spec(spec)
        sys.modules["import_fixer"] = import_fixer
        spec.loader.exec_module(import_fixer)
        
        # Run the import fixer
        fixer = import_fixer.ImportFixer()
        fixer.fix_project(project_root)
        return True
    except Exception as e:
        print(f"Error fixing imports: {str(e)}")
        return False

# Run import fixer first if requested
if len(sys.argv) > 1 and sys.argv[1] == 'fix-imports':
    try:
        src_path = Path(__file__).resolve().parent
        import_fixer_path = src_path / "GithubAnalyzer/utils/import_fixer.py"
        if import_fixer_path.exists():
            from GithubAnalyzer.utils.import_fixer import fix_project_imports
            fix_project_imports()
            sys.exit(0)
    except Exception as e:
        print(f"Error fixing imports: {str(e)}")
        sys.exit(1)

# Regular imports for other commands
from GithubAnalyzer.services.core.repo_processor import RepoProcessor
from GithubAnalyzer.services.core.database.database_service import DatabaseService
from GithubAnalyzer.models.core.database import CodebaseQuery
from GithubAnalyzer.utils.logging.logging_config import get_logger
from GithubAnalyzer.services.core.database.postgres_service import PostgresService
from GithubAnalyzer.config.db_config import get_db_config

logger = get_logger(__name__)

def process_repository(repo_url: str) -> None:
    """Process a GitHub repository and store its data."""
    try:
        processor = RepoProcessor()
        processor.process_repo(repo_url)
        print(f"Successfully processed repository: {repo_url}")
    except Exception as e:
        print(f"Error processing repository: {str(e)}")
        logger.exception("Repository processing failed")
        sys.exit(1)

def display_query_results(results: CodebaseQuery) -> None:
    """Display the results of a codebase query.
    
    Args:
        results: Query results containing semantic matches and relationships
    """
    print("\nSemantic Matches:")
    print("================")
    for snippet in results.semantic_matches:
        print(f"\nFile: {snippet.file_path}")
        print("Code snippet:")
        print("-" * 40)
        print(snippet.code_text)
        print("-" * 40)
    
    print("\nStructural Relationships:")
    print("=======================")
    for file_data in results.structural_relationships:
        print(f"\nFile: {file_data['file']}")
        for rel in file_data['relationships']:
            print(f"\nFunction: {rel['function']}")
            if rel['calls']:
                print("Calls:")
                for call in rel['calls']:
                    print(f"  - {call['function']} in {call['file']}")

def query_codebase(query: str, limit: Optional[int] = 5) -> None:
    """Query the processed codebase."""
    try:
        db_service = DatabaseService()
        results = db_service.query_codebase(query, limit=limit)
        display_query_results(results)
    except Exception as e:
        print(f"Error querying codebase: {str(e)}")
        logger.exception("Codebase query failed")
        sys.exit(1)

def cleanup_databases() -> None:
    """Clean up all databases."""
    try:
        db_service = DatabaseService()
        db_service.cleanup_databases()
        print("Successfully cleaned all databases.")
    except Exception as e:
        print(f"Error cleaning databases: {str(e)}")
        logger.exception("Database cleanup failed")
        sys.exit(1)

def initialize_databases() -> None:
    """Initialize database schemas and constraints."""
    try:
        db_service = DatabaseService()
        db_service.initialize_databases()
        print("Successfully initialized databases.")
    except Exception as e:
        print(f"Error initializing databases: {str(e)}")
        logger.exception("Database initialization failed")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="GitHub Repository Analyzer")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Process repository command
    process_parser = subparsers.add_parser('process', help='Process a GitHub repository')
    process_parser.add_argument('repo_url', help='GitHub repository URL')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query the processed codebase')
    query_parser.add_argument('query', help='Natural language query about the code')
    query_parser.add_argument('--limit', type=int, default=5, help='Maximum number of results')
    
    # Database management commands
    subparsers.add_parser('cleanup', help='Clean up all databases')
    subparsers.add_parser('init', help='Initialize database schemas and constraints')
    
    # Development commands
    subparsers.add_parser('fix-imports', help='Fix imports across the project')
    
    args = parser.parse_args()
    
    try:
        if args.command == 'process':
            process_repository(args.repo_url)
        elif args.command == 'query':
            query_codebase(args.query, args.limit)
        elif args.command == 'cleanup':
            cleanup_databases()
        elif args.command == 'init':
            initialize_databases()
        elif args.command == 'fix-imports':
            fix_imports_bootstrap()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        logger.exception("Command failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 