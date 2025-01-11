import pytest
from GithubAnalyzer.agents.ai_agent_cli import AIAgentCLI
from GithubAnalyzer.core.database_utils import DatabaseManager
from rich.console import Console
import os

console = Console()

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Setup test database with a sample repository"""
    console.print("[bold yellow]Setting up test database...[/bold yellow]")
    
    # Show current schema before any changes
    console.print("\n[bold blue]Current Database Schema:[/bold blue]")
    db_manager = DatabaseManager()
    try:
        # Clear both databases first
        console.print("\n[blue]Clearing existing data...[/blue]")
        db_manager.clear_all_data()
        db_manager.show_schema()
        
        # Clear the temp directory if it exists
        temp_dir = "./temp"
        if os.path.exists(temp_dir):
            console.print("\n[blue]Cleaning temp directory...[/blue]")
            import shutil
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
        
        # Initialize CLI and add test repository
        cli = AIAgentCLI()
        test_repo_url = "https://github.com/jerryjliu/llama_index"
        
        # Check if repository already exists
        if cli.db_manager.get_repository_info("llama_index"):
            console.print("\n[yellow]Repository already exists, skipping analysis[/yellow]")
        else:
            console.print("\n[blue]Analyzing new repository...[/blue]")
            cli.analyze_repo(test_repo_url)
        
        return cli
    finally:
        # Ensure proper cleanup
        db_manager.cleanup()

def test_repository_listing(setup_test_db):
    cli = setup_test_db
    try:
        # Test list_repositories
        console.print("\n[bold blue]Testing Repository Listing:[/bold blue]")
        cli.list_repositories()
        
        # Test detailed status for each repo
        repos = cli.db_manager.get_active_repositories()
        if repos:
            console.print("\n[bold blue]Detailed Repository Status:[/bold blue]")
            for repo in repos:
                cli.show_repository_status(repo['name'])
        else:
            console.print("\n[yellow]No repositories found in database[/yellow]")
        
        # Test database verification
        console.print("\n[bold blue]Database Verification:[/bold blue]")
        cli.verify_analysis()
    finally:
        # Ensure proper cleanup of CLI resources
        if hasattr(cli, 'db_manager'):
            cli.db_manager.cleanup() 