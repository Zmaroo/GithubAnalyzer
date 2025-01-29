# GithubAnalyzer

A tool for analyzing GitHub repositories using tree-sitter and custom parsers.

## Overview

GithubAnalyzer is designed to be used as a library by AI agents for analyzing code repositories. It provides comprehensive code analysis capabilities including:

- Semantic code search
- AST-based code analysis
- Custom parsing for configuration files
- Code structure analysis
- Language detection and support

## Entry Point

The main entry point for AI agents is through the `DatabaseService` class in `src/GithubAnalyzer/services/core/database/database_service.py`. This service provides all necessary functionality for:

- Repository analysis
- Code querying
- Database management
- Language support information

Example usage:
```python
from GithubAnalyzer.services.core.database.database_service import DatabaseService

# Initialize the service
db_service = DatabaseService()

# Initialize databases (first time only)
db_service.initialize_databases()

# Analyze a repository
repo_id = db_service.analyze_repository("https://github.com/user/repo")

# Query the codebase
results = db_service.semantic_code_search("Find all database connections", limit=5)
```

## Development Tools

For development purposes, utility scripts are available in `src/GithubAnalyzer/utils/dev_tools.py`:

```bash
# Fix import statements across the project
python -m GithubAnalyzer.utils.dev_tools fix-imports
```

## Dependencies

- Python 3.8+
- tree-sitter
- PostgreSQL with pgvector extension
- Neo4j with APOC and GDS plugins

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see `.env.example`)
4. Initialize databases: Use `DatabaseService.initialize_databases()`

## Features

- Parse code using tree-sitter for accurate syntax analysis
- Support for multiple programming languages
- Clean and modular architecture

## Project Structure

```text
src/GithubAnalyzer/
├── models/
│   ├── core/
│   │   ├── base.py      # Base model classes
│   │   └── errors.py    # Core error definitions
│   └── analysis/
│       ├── ast.py       # AST models
│       ├── results.py   # Analysis results
│       └── code.py      # Code structure models
├── services/
│   └── core/
│       ├── parsers/     # Tree-sitter parser implementations
│       ├── parser_service.py  # Main parser service
│       └── configurable.py    # Service configuration
└── utils/
    ├── context_manager.py  # Resource management
    ├── file_utils.py       # File operations
    ├── logging.py          # Logging utilities
    └── decorators.py       # Code organization
```

## Testing

Run parser tests:

```bash
pytest tests/test_parsers -v
```

## Development

1. Install development dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

2. Run linters and type checkers:

   ```bash
   black .
   isort .
   mypy .
   pylint src/GithubAnalyzer
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## License

[MIT License](LICENSE)
