# Logging Architecture Strategy

## Context

The current logging implementation for the TreeSitterTraversal class exhibits several architectural anti-patterns:

1. **Logger Hierarchy Conflict**  
   - Module-level logger ('tree_sitter.traversal') conflicts with parent logger configuration
   - Disabled propagation prevents hierarchical logging configuration

2. **Handler Proliferation**  
   - Each class instance creates duplicate handlers
   - No thread-safe handling of log file access

3. **Error Visibility**  
   - Swallowed exceptions in error handling paths
   - No structured error diagnostics

## Decision

Implement a centralized logging architecture with:

1. **Hierarchical Logger Configuration**

```python
# Configure at application startup
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'tree_sitter': {
            'level': 'INFO',
            'propagate': True,
        }
    }
})
```

1. **Singleton Handler Registration**

```python
# In core/utils/logging.py
def configure_tree_sitter_logging():
    root_logger = logging.getLogger('tree_sitter')
    if not any(isinstance(h, TreeSitterLogHandler) for h in root_logger.handlers):
        handler = TreeSitterLogHandler()
        handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(handler)
```

1. **Structured Error Reporting**

```python
class StructuredFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "thread": record.thread,
            "message": record.getMessage(),
            "context": getattr(record, 'context', {})
        })
```

## Consequences

- All tree-sitter related loggers inherit from 'tree_sitter' root
- Single handler instance shared across all components
- Thread-safe logging through QueueHandler/QueueListener pattern
- Structured logs enable automated analysis
- Centralized configuration reduces code duplication
