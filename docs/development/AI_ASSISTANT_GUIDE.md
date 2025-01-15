# Guide for AI Assistants

## Project Overview

This is an enterprise-grade GitHub repository analyzer designed to provide AI assistants with deep understanding of codebases.

## Quick Start

1. Review these files first:
   - docs/development/OVERVIEW.md (Project status)
   - dev_logs/2024_03_tree_sitter.md (Current development)
   - docs/project_structure.md (Code organization)

2. Key Components:
   - Tree-sitter Parser: src/GithubAnalyzer/services/core/parsers/tree_sitter.py
   - Parser Service: src/GithubAnalyzer/services/core/parser_service.py
   - Test Suite: tests/test_parsers/

3. Current Development Focus:
   - Advanced Tree-sitter parsing
   - Test failures in test_tree_sitter_advanced.py
   - Memory optimization

4. Development Workflow:
   - Check dev_logs/ for latest status
   - Review failing tests before making changes
   - Update dev logs after significant changes
   - Maintain type hints and documentation

## Important Notes

- Project is AI model agnostic
- Focus on maintainable, typed code
- Heavy emphasis on testing
- Documentation is critical
