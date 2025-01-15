# Testing Guide

## Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_parser_initialization.py -v

# Run with coverage
pytest tests/unit/ --cov=GithubAnalyzer
```

### Test Categories

```plaintext
tests/
├── unit/                    # Unit tests
│   ├── test_parser_*.py     # Parser unit tests
│   └── test_services_*.py   # Service unit tests
├── integration/            # Integration tests
│   ├── conftest.py         # Integration test fixtures
│   └── test_*_integration.py
├── security/              # Security tests
│   ├── conftest.py        # Security test fixtures
│   └── test_*_security.py
└── performance/          # Performance tests
    ├── conftest.py       # Performance test fixtures
    ├── test_analyzer_performance.py
    └── test_tree_sitter_performance.py
```

## Test Fixtures

Each test category has its own fixtures in `conftest.py`:

- Unit: Basic parser initialization
- Integration: Multi-language parser setup
- Performance: Optimized parser configuration
- Security: Hardened parser instance

## Running Tests by Category

```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run performance tests
pytest tests/performance -v

# Run security tests
pytest tests/security -v
```

1. Unit Tests
   - Basic parser setup
   - Language loading
   - Configuration validation

### Coverage Requirements

- Minimum coverage: 80%
- Critical paths: 100%
- Error handlers: 100%
