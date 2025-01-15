# GithubAnalyzer Development Overview

## Project Purpose

GithubAnalyzer is an enterprise-grade tool designed to provide deep, comprehensive analysis of GitHub repositories. The goal is to create a backend that can provide AI assistants/models with complete understanding of codebases, enabling them to effectively assist in development.

### Key Features (Planned)

- Advanced Tree-sitter AST analysis
- Semantic code analysis
- Structural relationship mapping
- Documentation analysis
- Graph-based repository relationships
- Vector-based code similarity

### Technology Stack

- Tree-sitter for AST parsing
- Neo4j (with Graph Data Science & APOC) for graph analysis
- PostgreSQL with pgvector for vector similarity
- Redis for caching
- Python 3.9+ backend

## Current Development Status

### Completed

- Basic project structure
- Tree-sitter parser implementation
- Core service architecture
- Error handling
- Logging system

### In Progress

- Advanced Tree-sitter methods
- AST analysis capabilities
- Parser service refinements

### Next Steps

1. Database integration (Neo4j, PostgreSQL)
2. Vector embedding system
3. Graph analysis capabilities
4. Query interfaces

## Current Development State (Last Updated: March 2024)

### Active Development

- Working on advanced Tree-sitter parsing capabilities
- Fixing test failures in test_tree_sitter_advanced.py
- Optimizing cursor operations and memory usage

### Known Issues

- Tree-sitter query timeouts on complex structures
- Memory management with large ASTs
- Inconsistent error handling across languages

### Entry Points for New Development

1. Start with src/GithubAnalyzer/services/core/parsers/tree_sitter.py
2. Review test failures in tests/test_parsers/test_tree_sitter_advanced.py
3. Check dev_logs/2024_03_tree_sitter.md for latest status

## Architecture Notes

- Modular design for AI model agnosticism
- Focus on extensibility and maintainability
- Strong typing and error handling
- Comprehensive documentation

### Component Responsibilities

1. Models
   - Define data structures
   - Handle validation
   - Define error types

2. Services
   - Implement business logic
   - Handle resource management
   - Provide clean interfaces

3. Utils
   - Share common functionality
   - Handle cross-cutting concerns
   - Provide infrastructure support

4. Config
   - Manage application settings
   - Handle environment configuration
   - Define feature flags
