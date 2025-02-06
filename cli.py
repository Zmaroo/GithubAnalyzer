import argparse

from GithubAnalyzer.services.core.database.database_service import DatabaseService


def main():
    parser = argparse.ArgumentParser(description='GitHub Analyzer CLI')
    parser.add_argument('--reset-database', action='store_true', help='Reset both PostgreSQL and Neo4j databases')
    # You can add more command-line arguments here as needed
    args = parser.parse_args()

    db_service = DatabaseService()

    if args.reset_database:
        print('Resetting databases...')
        db_service.reset_databases()
        print('Databases have been reset.')

    # Other CLI commands can be added here. For now, we'll exit after processing the reset flag.


if __name__ == '__main__':
    main() 