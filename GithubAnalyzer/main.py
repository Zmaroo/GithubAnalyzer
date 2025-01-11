import click
from .core.registry import BusinessTools
from .core.utils import setup_logger

logger = setup_logger(__name__)

@click.group()
def cli():
    """GitHub Code Analysis Tool CLI"""
    pass

@cli.command()
@click.argument('repo_url')
def analyze(repo_url):
    """Analyze a GitHub repository"""
    tools = BusinessTools.create()
    result = tools.repo_manager.analyze_repo(repo_url)
    click.echo(f"Analysis complete: {result['name']}")

@cli.command()
@click.argument('question')
def query(question):
    """Query the analyzed repository"""
    tools = BusinessTools.create()
    response = tools.query_processor.query_repository(question)
    click.echo(f"Answer: {response.response}")
    if response.confidence < 0.5:
        click.echo("(Note: Low confidence response)")

@cli.command()
def status():
    """Show repository status"""
    tools = BusinessTools.create()
    repos = tools.db_manager.get_active_repositories()
    if repos:
        click.echo("\nAnalyzed repositories:")
        for repo in repos:
            click.echo(f"  - {repo['name']} (Last analyzed: {repo['last_analyzed']})")
    else:
        click.echo("No repositories analyzed yet")

@cli.command()
def clear():
    """Clear all stored data"""
    tools = BusinessTools.create()
    tools.db_manager.clear_all_data()
    click.echo("All data cleared")

def main():
    try:
        cli()
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    return 0

if __name__ == '__main__':
    exit(main()) 