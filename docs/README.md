# GitHub Code Analysis Tool

A tool for analyzing and processing GitHub repositories using AI-enhanced code analysis.

## Overview

This tool provides advanced code analysis capabilities for GitHub repositories, including:

- Code structure and pattern analysis
- Documentation analysis
- Framework detection and analysis
- AI-powered code understanding

## Components

### Core Components

- **Code Analyzer**: Analyzes code structure, patterns, and relationships
- **Documentation Analyzer**: Processes and analyzes documentation files
- **Database Utils**: Manages data storage in PostgreSQL and Neo4j
- **Tree Sitter Utils**: Provides language parsing capabilities
- **Framework Analyzers**: Detects and analyzes framework usage

### AI Agents

- **AI Agent CLI**: Command-line interface for interacting with the analysis tools
- **AI Agent Enhanced**: Core AI functionality for code understanding

### Database Layer

- PostgreSQL: Stores code snippets and documentation
- Neo4j: Stores code relationships and dependencies
- Redis: Caching layer for improved performance

### Development Tools

- manage_db.py: Database management tool for development

## Development

### Project Structure

```text
GithubAnalyzer/
├── core/           # Core analysis modules
├── agents/         # AI agent implementations
├── config/         # Configuration files
└── db/            # Database management
```

### Dependencies

- Python 3.8+
- Tree-sitter
- PostgreSQL
- Neo4j
- Redis
- Sentence Transformers

### Docker Integration

The project includes Docker configuration for:

- Development environment setup
- n8n workflow integration
- Database services

## Usage

1. **Command Line Interface**

   ```bash
   python -m GithubAnalyzer.agents.ai_agent_cli
   ```

2. **Available Commands**
   - `analyze <repo_url>`: Analyze a new repository
   - `ask <question>`: Query about analyzed repository
   - `status`: Check analysis status
   - `use <repo_name>`: Switch to analyzed repository

## Configuration

- Environment variables in `.env`
- Database configurations in `config.py`
- n8n configurations:
  - Workflows and data in `n8n_data/`
  - Encryption key in `n8n_data/config`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[License Type] - See LICENSE file for details
