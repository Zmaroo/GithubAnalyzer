"""GitHub Code Analysis Tool CLI"""

import logging
import sys
from pathlib import Path

import click

from .models.errors import AnalysisError, ValidationError
from .utils.bootstrap import Bootstrap
from .utils.logging import configure_logging

logger = logging.getLogger(__name__)


def init_app(log_level: str = "INFO") -> None:
    """Initialize application"""
    try:
        # Configure logging
        log_file = Path("logs/github_analyzer.log")
        configure_logging(log_level=log_level, log_file=str(log_file))

        # Initialize application
        return Bootstrap.initialize()
    except Exception as e:
        logger.critical(f"Failed to initialize application: {e}")
        sys.exit(1)


@click.group()
@click.option("--log-level", default="INFO", help="Logging level")
def cli(log_level: str):
    """GitHub Code Analysis Tool CLI"""
    init_app(log_level)


@cli.command()
@click.argument("repo_url")
def analyze(repo_url: str):
    """Analyze a GitHub repository"""
    try:
        registry = init_app()
        result = registry.analyzer_service.analyze_repository(repo_url)
        click.echo(f"Analysis complete: {result.name}")
    except (AnalysisError, ValidationError) as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        logger.exception("Unexpected error during analysis")
        sys.exit(1)


def main():
    """CLI entry point"""
    try:
        cli()
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
