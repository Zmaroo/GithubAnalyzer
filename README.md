# GithubAnalyzer

A tool for analyzing GitHub repositories using tree-sitter parsing.

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

## Installation

1. Install Python 3.9 or higher
2. Clone this repository
3. Install dependencies:

   ```bash
   pip install -e .
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
