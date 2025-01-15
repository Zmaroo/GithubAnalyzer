# Project Structure

```text
src/GithubAnalyzer/
├── config/                     # Configuration
│   ├── __init__.py
│   ├── language_config.py      # Language-specific config
│   └── settings.py            # Global settings
├── models/                    # Data models
│   ├── __init__.py
│   ├── analysis/             # Analysis models
│   │   ├── __init__.py
│   │   ├── ast.py           # AST representation
│   │   └── results.py       # Analysis results
│   └── core/                # Core models
│       ├── __init__.py
│       ├── base.py          # Base model classes
│       ├── config/          # Configuration models
│       │   ├── __init__.py
│       │   └── settings.py  # Settings model
│       └── errors.py        # Error definitions
├── services/                 # Service layer
│   ├── __init__.py
│   ├── base.py              # Base service
│   ├── errors.py            # Service errors
│   └── core/                # Core services
│       ├── __init__.py
│       ├── configurable.py  # Service configuration
│       ├── parser_service.py # Main parser service
│       ├── parsers/         # Parser implementations
│       │   ├── __init__.py
│       │   ├── base.py      # Base parser
│       │   ├── config.py    # Config parser
│       │   ├── documentation.py # Doc parser
│       │   ├── license.py   # License parser
│       │   └── tree_sitter.py # Tree-sitter parser
│       └── utils/           # Service utilities
│           └── file_utils.py # File operations
├── utils/                   # Utilities
│   ├── __init__.py
│   ├── context_manager.py   # Resource management
│   ├── decorators.py       # Code organization
│   ├── file_utils.py       # File operations
│   └── logging.py          # Logging utilities
├── py.typed                # Type hint marker
└── version.py             # Version information

tests/                     # Test suite
├── conftest.py           # Test configuration
├── integration/          # Integration tests
├── performance/          # Performance tests
├── security/            # Security tests
├── test_parsers/        # Parser tests
└── unit/               # Unit tests

logs/                    # Log files
└── .gitkeep            # Keep empty directory
```

Key Components:

- `config/`: Application configuration
- `models/`: Data models and type definitions
- `services/`: Core business logic and services
- `utils/`: Shared utilities and helpers
- `tests/`: Test suite organized by type
- `logs/`: Application logs (gitignored except .gitkeep)
