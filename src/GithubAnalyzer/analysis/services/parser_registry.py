"""Service for registering analysis parsers with core parser service."""

from typing import Optional

from ..core.parser_service import ParserService
from ..common.cache_service import CacheService
from ...utils.context_manager import ContextManager
from .parsers.tree_sitter import TreeSitterParser
from .parsers.documentation import DocumentationParser
from .parsers.license import LicenseParser


class ParserRegistry:
    """Registry for analysis parsers."""
    
    def __init__(
        self,
        parser_service: ParserService,
        cache_service: Optional[CacheService] = None,
        context_manager: Optional[ContextManager] = None
    ):
        """Initialize parser registry.
        
        Args:
            parser_service: Core parser service to register parsers with
            cache_service: Optional cache service instance
            context_manager: Optional context manager instance
        """
        self._parser_service = parser_service
        self._cache = cache_service
        self._context = context_manager
        
    def register_parsers(self) -> None:
        """Register all analysis parsers with core parser service."""
        # Tree-sitter parser for code analysis
        tree_sitter = TreeSitterParser(
            cache_service=self._cache,
            context_manager=self._context
        )
        tree_sitter.initialize()
        self._parser_service.register_parser("tree-sitter", tree_sitter)
        
        # Documentation parser
        documentation = DocumentationParser()
        documentation.initialize()
        self._parser_service.register_parser("documentation", documentation)
        
        # License parser
        license_parser = LicenseParser()
        license_parser.initialize()
        self._parser_service.register_parser("license", license_parser) 