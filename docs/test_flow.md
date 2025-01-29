# Test Flow Documentation

This document outlines the test flow and all files involved when running the test suite.

## 1. Initial Setup

```bash
src/GithubAnalyzer/utils/logging/
├── logging_config.py      # Configures logging
├── logger_factory.py      # Creates loggers
├── formatters.py         # Formats log messages
└── tree_sitter_logging.py # Tree-sitter specific logging
```

## 2. Core Database Services

```bash
src/GithubAnalyzer/services/core/database/
├── database_service.py    # Main database interface
├── postgres_service.py    # PostgreSQL operations
├── neo4j_service.py       # Neo4j operations
├── embedding_service.py   # Code embedding generation
└── db_config.py          # Database configuration
```

## 3. Repository Processing

```bash
src/GithubAnalyzer/services/core/
├── repo_processor.py      # Handles repository cloning and processing
├── parser_service.py      # Main parsing service
└── file_service.py       # File operations
```

## 4. Parser Services

```bash
src/GithubAnalyzer/services/analysis/parsers/
├── language_service.py    # Language detection and support
├── query_service.py       # Tree-sitter query handling
├── traversal_service.py   # AST traversal
└── tree_sitter_editor.py  # Code editing
```

## 5. Models

```bash
src/GithubAnalyzer/models/
├── core/
│   ├── ast.py            # AST models
│   ├── database.py       # Database models
│   ├── errors.py         # Error definitions
│   └── file.py           # File models
└── analysis/
    ├── code_analysis.py  # Code analysis models
    └── results.py        # Analysis results models
```

## Test Flow

### 1. Repository Analysis Test (`test_repository_analysis(repo_url)`)

- Initializes databases
- Processes repository using `RepoProcessor`
- Verifies repository storage in PostgreSQL
- Tests semantic search
- Tests codebase querying

### 2. Code Analysis Test (`test_code_analysis()`)

- Tests language detection
- Tests code structure analysis
- Tests AST traversal
- Tests query patterns

### 3. Code Editing Test (`test_code_editing()`)

- Tests code parsing
- Tests code editing operations
- Verifies edit results
- Checks syntax validity

### 4. Language Support Test (`test_language_support()`)

- Tests supported languages
- Verifies language features
- Checks file extension support

## Key Dependencies

1. Tree-sitter language pack
2. PostgreSQL database
3. Neo4j database
4. Python packages:
   - `psycopg2` for PostgreSQL
   - `neo4j` for Neo4j
   - `tree-sitter` for parsing
   - `numpy` for embeddings

The test suite verifies the entire pipeline from repository processing to code analysis and editing, ensuring all components work together correctly.
