"""Context management utilities for resource handling."""

from pathlib import Path
from typing import Any, Dict, Optional, Set
from threading import Lock


class ContextManager:
    """Manages context and resources for analysis operations."""

    def __init__(self):
        """Initialize context manager."""
        self._resources: Dict[str, Any] = {}
        self._active = False
        self._lock = Lock()
        
        # Parser caches
        self._ast_cache: Dict[str, Any] = {}
        self._parser_instances: Dict[str, Any] = {}
        self._loaded_languages: Set[str] = set()
        
        # File caches
        self._file_info_cache: Dict[str, Dict] = {}
        self._max_cache_size = 1000
        
        # Memory management
        self._memory_limit = 1024 * 1024 * 1024  # 1GB
        self._current_memory = 0

    def start(self) -> None:
        """Start context and initialize resources."""
        with self._lock:
            if not self._active:
                self._active = True
                self._initialize_resources()

    def stop(self) -> None:
        """Stop context and cleanup resources."""
        with self._lock:
            if self._active:
                self._cleanup_resources()
                self._active = False

    def get_resource(self, name: str) -> Any:
        """Get a resource by name.

        Args:
            name: Resource name.

        Returns:
            Resource data.

        Raises:
            KeyError: If resource not found.
            RuntimeError: If context manager not active.
        """
        if not self._active:
            raise RuntimeError("Context manager not active.")
        return self._resources[name]

    def cache_ast(self, file_path: Path, ast: Any) -> None:
        """Cache AST for a file.
        
        Args:
            file_path: Path to the source file
            ast: The AST to cache
        """
        with self._lock:
            key = str(file_path.resolve())
            self._ast_cache[key] = {
                'ast': ast,
                'mtime': file_path.stat().st_mtime
            }
            self._cleanup_cache_if_needed()

    def get_cached_ast(self, file_path: Path) -> Optional[Any]:
        """Get cached AST if available and still valid.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            Cached AST or None if not found/invalid
        """
        with self._lock:
            key = str(file_path.resolve())
            cached = self._ast_cache.get(key)
            if cached and file_path.stat().st_mtime == cached['mtime']:
                return cached['ast']
        return None

    def register_parser(self, language: str, parser: Any) -> None:
        """Register a parser instance.
        
        Args:
            language: Language identifier
            parser: Parser instance
        """
        with self._lock:
            self._parser_instances[language] = parser
            self._loaded_languages.add(language)

    def get_parser(self, language: str) -> Optional[Any]:
        """Get registered parser for a language.
        
        Args:
            language: Language identifier
            
        Returns:
            Parser instance or None if not found
        """
        return self._parser_instances.get(language)

    def cache_file_info(self, file_path: Path, info: Dict) -> None:
        """Cache file information.
        
        Args:
            file_path: Path to the file
            info: File information dictionary
        """
        with self._lock:
            key = str(file_path.resolve())
            self._file_info_cache[key] = {
                'info': info,
                'mtime': file_path.stat().st_mtime
            }
            self._cleanup_cache_if_needed()

    def get_cached_file_info(self, file_path: Path) -> Optional[Dict]:
        """Get cached file information if still valid.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Cached file info or None if not found/invalid
        """
        with self._lock:
            key = str(file_path.resolve())
            cached = self._file_info_cache.get(key)
            if cached and file_path.stat().st_mtime == cached['mtime']:
                return cached['info']
        return None

    def _initialize_resources(self) -> None:
        """Initialize required resources."""
        self._resources = {
            'ast_cache': self._ast_cache,
            'parser_instances': self._parser_instances,
            'loaded_languages': self._loaded_languages,
            'file_info_cache': self._file_info_cache
        }

    def _cleanup_resources(self) -> None:
        """Cleanup allocated resources."""
        # Clear caches
        self._ast_cache.clear()
        self._file_info_cache.clear()
        
        # Cleanup parser instances
        for parser in self._parser_instances.values():
            if hasattr(parser, 'cleanup'):
                parser.cleanup()
        self._parser_instances.clear()
        
        # Clear other resources
        self._loaded_languages.clear()
        self._resources.clear()
        self._current_memory = 0

    def _cleanup_cache_if_needed(self) -> None:
        """Clean up caches if memory limit exceeded."""
        if len(self._ast_cache) > self._max_cache_size:
            # Remove oldest entries
            items = sorted(
                self._ast_cache.items(),
                key=lambda x: x[1]['mtime']
            )
            for key, _ in items[:len(items) // 2]:
                del self._ast_cache[key]

        if len(self._file_info_cache) > self._max_cache_size:
            items = sorted(
                self._file_info_cache.items(),
                key=lambda x: x[1]['mtime']
            )
            for key, _ in items[:len(items) // 2]:
                del self._file_info_cache[key]
