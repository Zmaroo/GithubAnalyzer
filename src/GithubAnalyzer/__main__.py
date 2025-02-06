#!/usr/bin/env python
import argparse

from GithubAnalyzer.services.core.database.database_service import \
    DatabaseService


def main():
    parser = argparse.ArgumentParser(description='GitHub Analyzer CLI')
    parser.add_argument('--reinit', action='store_true', help='Reinitialize the databases')
    parser.add_argument('--analyze', type=str, help='Analyze a repository (provide repo URL or directory path)')
    args = parser.parse_args()

    ds = DatabaseService()

    if args.reinit:
        print('Reinitializing databases...')
        ds.initialize_databases()
        print('Databases reinitialized.')

    if args.analyze:
        repo = args.analyze
        print(f'Analyzing repository: {repo}')
        repo_id = ds.analyze_repository(repo)
        print(f'Analysis complete. Repository ID: {repo_id}')


if __name__ == '__main__':
    main() 