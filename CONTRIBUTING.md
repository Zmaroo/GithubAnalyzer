# Contributing to GithubAnalyzer

## Development Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/GithubAnalyzer.git
cd GithubAnalyzer
```

1. Install in development mode with all dependencies:

```bash
pip install -e ".[dev]"
```

This will install:

- All required tree-sitter language parsers
- Development dependencies (pytest, black, etc.)
- Core dependencies

1. Run tests:

```bash
pytest
```
