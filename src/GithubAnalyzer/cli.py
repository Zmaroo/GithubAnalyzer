#!/usr/bin/env python3
"""Command Line Interface for GithubAnalyzer.

This module provides a CLI for interacting with the GithubAnalyzer system.
It supports both human users and AI agents with commands for:
- Database operations
- Repository analysis
- Code search and analytics
- System information
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import click

from GithubAnalyzer.services.core.database.database_service import \
    DatabaseService
from GithubAnalyzer.utils.logging import get_logger

# Initialize logger
logger = get_logger("cli")

# Initialize database service
db_service = DatabaseService()

@click.group()
def cli():
    """GithubAnalyzer CLI - Manage and analyze code repositories."""
    pass

# Database Commands
@cli.group()
def db():
    """Database management commands."""
    pass

@db.command()
def init():
    """Initialize the databases."""
    try:
        db_service.initialize_databases()
        click.echo("Databases initialized successfully.")
    except Exception as e:
        click.echo(f"Error initializing databases: {str(e)}", err=True)

@db.command()
def clear():
    """Clear all databases."""
    try:
        db_service.cleanup_databases()
        click.echo("Databases cleared successfully.")
    except Exception as e:
        click.echo(f"Error clearing databases: {str(e)}", err=True)

@db.command()
def reset():
    """Reset both PostgreSQL and Neo4j databases (clear then initialize)."""
    try:
        db_service.reset_databases()
        click.echo("Databases have been reset successfully.")
    except Exception as e:
        click.echo(f"Error resetting databases: {str(e)}", err=True)

@db.command()
def info():
    """Show information about the database state."""
    try:
        db = DatabaseService()
        info = db.pg_service.get_database_info()
        
        # Display repository information
        click.echo("\nRepository Information:")
        click.echo(f"Total repositories: {info['repository_count']}")
        click.echo(f"Total unique files: {info['file_count']}")
        
        # Display language information
        click.echo("\nLanguage Distribution:")
        if info['language_distribution']:
            total_snippets = sum(info['language_distribution'].values())
            for lang, count in info['language_distribution'].items():
                percentage = (count / total_snippets) * 100
                click.echo(f"{lang}: {count} snippets ({percentage:.1f}%)")
        else:
            click.echo("No code snippets found in the database.")
        
        # Display supported languages
        click.echo("\nSupported Languages:")
        if info['languages']:
            for lang in sorted(info['languages']):
                click.echo(f"- {lang}")
        else:
            click.echo("No languages configured.")
            
    except Exception as e:
        click.echo(f"Error getting database info: {str(e)}", err=True)
    finally:
        if 'db' in locals():
            db.pg_service.disconnect()
            db.neo4j_service.close()

# Repository Commands
@cli.group()
def repo():
    """Repository management commands."""
    pass

@repo.command()
@click.argument('url')
@click.option('--data-dir', type=click.Path(), help='Directory for test data')
def analyze(url: str, data_dir: Optional[str] = None):
    """Analyze a repository."""
    try:
        # If using test data, construct file URL
        if data_dir:
            url = f"file://{Path(data_dir).absolute()}"
            
        repo_id = db_service.analyze_repository(url)
        click.echo(f"Repository analyzed successfully. ID: {repo_id}")
    except Exception as e:
        click.echo(f"Error analyzing repository: {str(e)}", err=True)

@repo.command()
@click.argument('repo_id', type=int)
def info(repo_id: int):
    """Show repository information."""
    try:
        info = db_service.get_stored_data(repo_id)
        click.echo(f"\nRepository {repo_id} Overview:")
        click.echo("=======================")
        
        # Format and display the info
        click.echo(json.dumps(info, indent=2))
    except Exception as e:
        click.echo(f"Error getting repository info: {str(e)}", err=True)

@repo.command()
@click.argument('repo_id', type=int)
def analyze_structure(repo_id: int):
    """Analyze code structure of a repository."""
    try:
        analysis = db_service.analyze_code_structure(repo_id)
        click.echo("\nCode Structure Analysis:")
        click.echo("=======================")
        
        # Dependencies
        click.echo("\nDependencies:")
        for comp in analysis['dependencies']['central_components']:
            click.echo(f"  - {comp['name']} (score: {comp['score']:.2f})")
            
        # Communities
        click.echo("\nCode Communities:")
        for name, members in analysis['communities'].items():
            click.echo(f"\n  {name}:")
            for member in members:
                click.echo(f"    - {member}")
                
        # Critical Paths
        click.echo("\nCritical Paths:")
        for path in analysis['critical_paths']:
            click.echo(f"  {' -> '.join(path)}")
            
    except Exception as e:
        click.echo(f"Error analyzing code structure: {str(e)}", err=True)

# Search Commands
@cli.group()
def search():
    """Code search commands."""
    pass

@search.command()
@click.argument('query')
@click.option('--repo-id', type=int, help='Limit search to specific repository')
@click.option('--limit', type=int, default=5, help='Maximum number of results')
def code(query: str, repo_id: Optional[int], limit: int):
    """Search code using natural language."""
    try:
        results = db_service.semantic_code_search(query, limit, repo_id)
        click.echo("\nSearch Results:")
        click.echo("===============")
        
        for i, result in enumerate(results, 1):
            click.echo(f"\n{i}. File: {result['file_path']}")
            click.echo(f"   Score: {result['score']:.2f}")
            click.echo(f"   Language: {result['language']}")
            click.echo(f"   Snippet:")
            click.echo("   " + "\n   ".join(result['code_text'].split('\n')))
            
    except Exception as e:
        click.echo(f"Error searching code: {str(e)}", err=True)

@search.command()
@click.argument('pattern')
@click.option('--repo-id', type=int, help='Limit search to specific repository')
@click.option('--limit', type=int, default=5, help='Maximum number of results')
def pattern(pattern: str, repo_id: Optional[int], limit: int):
    """Search for similar code patterns."""
    try:
        results = db_service.find_similar_patterns(pattern, limit)
        click.echo("\nPattern Search Results:")
        click.echo("======================")
        
        for i, result in enumerate(results, 1):
            click.echo(f"\n{i}. File: {result['file_path']}")
            click.echo(f"   Similarity: {result['similarity']:.2f}")
            click.echo(f"   Pattern:")
            click.echo("   " + "\n   ".join(result['pattern'].split('\n')))
            
    except Exception as e:
        click.echo(f"Error searching patterns: {str(e)}", err=True)

if __name__ == '__main__':
    cli() 