# Development Guidelines

## Core Principles

1. Single Source of Truth
   - Configuration: src/GithubAnalyzer/config/settings.py
   - Logging: src/GithubAnalyzer/utils/logging.py
   - Error Handling: src/GithubAnalyzer/models/core/errors.py

2. Service Organization
   - Core services go in services/core/
   - Base classes end with _base (e.g., service_base.py)
   - Implementation classes in descriptive directories (e.g., parsers/)

3. Logging Guidelines
   - NEVER create custom loggers
   - ALWAYS use application logger from utils.logging
   - ALL logs must go to logs/ directory
   - Use appropriate log levels:
     - DEBUG: Detailed debugging info
     - INFO: General operational events
     - WARNING: Unexpected but handled events
     - ERROR: Errors that need attention
     - CRITICAL: System-level failures

4. Directory Structure

   ```plaintext
   src/GithubAnalyzer/
   ├── config/                 # Application configuration
   │   ├── language_config.py  # Language-specific settings
   │   └── settings.py         # Global settings
   ├── models/
   │   ├── analysis/          # Analysis-specific models
   │   │   ├── ast.py         # AST data structures
   │   │   └── results.py     # Analysis results
   │   └── core/              # Core model definitions
   │       ├── base.py        # Base model classes
   │       ├── errors.py      # Error definitions
   │       └── config/        # Configuration models
   └── services/
       └── core/
           ├── base_service.py  # Base service definition
           ├── configurable.py  # Configuration mixin
           ├── parser_service.py # High-level parser service
           └── parsers/         # Parser implementations
               ├── base.py      # Base parser interface
               └── tree_sitter.py # Tree-sitter implementation
           └── utils/                   # Shared utilities
               ├── file_utils.py        # File operations
               ├── logging.py           # Logging configuration
               ├── context_manager.py   # Context managers
               └── decorators.py        # Shared decorators
   ```

5. Import Hierarchy
   - Models → Utils → Services → Applications
   - Avoid circular dependencies
   - Use relative imports within modules
   - Use absolute imports across modules

6. Testing
   - Test Organization:
     - Unit tests for individual components
     - Integration tests for component interaction
     - Performance tests for optimization
     - Security tests for vulnerability checks
   - Test Fixtures:
     - Category-specific fixtures in conftest.py
     - Shared fixtures in root conftest.py
     - Clean resource management
   - Test Naming:
     - test_*_unit.py for unit tests
     - test_*_integration.py for integration
     - test_*_performance.py for performance
     - test_*_security.py for security

7. Service Organization Rules
   - Single responsibility: Each module has one clear purpose
   - DRY: No duplicated functionality across modules
   - Centralized utilities: All utils in utils/ package
   - Clear hierarchy: Models → Utils → Services
