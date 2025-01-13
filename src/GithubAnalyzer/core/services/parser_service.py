"""Parser service for handling file parsing"""
from typing import Dict, Any, Optional, List
from pathlib import Path
from ..parsers.base import BaseParser
from ..parsers.tree_sitter import TreeSitterParser
from ..parsers.custom import (
    ConfigParser,
    DocumentationParser,
    LicenseParser
)
from .configurable import ConfigurableService, ServiceConfig
from .base import FileParsingError
from ..utils.logging import setup_logger
from ..models.base import ParseResult
from dataclasses import dataclass, field

logger = setup_logger(__name__)

@dataclass
class ParserConfig(ServiceConfig):
    """Parser service configuration"""
    max_file_size: int = 1024 * 1024  # 1MB
    supported_extensions: List[str] = field(default_factory=lambda: ['.py', '.js', '.yml', '.md'])
    enable_caching: bool = True
    cache_ttl: int = 3600

class ParserService(ConfigurableService):
    """Service for parsing files"""
    
    def __init__(self, registry=None, config: Optional[ParserConfig] = None):
        """Initialize parser service"""
        self.parsers: List[BaseParser] = []
        super().__init__(registry, config or ParserConfig())
        
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize parsers"""
        try:
            if config:
                self._update_config(config)
                
            self.parsers = [
                TreeSitterParser(),
                ConfigParser(),
                DocumentationParser(),
                LicenseParser()
            ]
        except Exception as e:
            raise FileParsingError(f"Failed to initialize parsers: {e}")
        
    def parse_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Parse file content"""
        if not self.initialized:
            raise FileParsingError("Parser service not initialized")
            
        try:
            # Check if file exists first
            if not Path(file_path).exists():
                raise FileParsingError(f"File not found: {file_path}")
                
            # Check file size
            if Path(file_path).stat().st_size > self.service_config.max_file_size:
                raise FileParsingError(f"File too large: {file_path}")
                
            # Try each parser
            for parser in self.parsers:
                if parser.can_parse(file_path):
                    result = parser.parse_file(file_path, content)
                    if isinstance(result, dict):
                        return result
                    return result.to_dict()
                    
            # No suitable parser found
            return {
                'success': False,
                'ast': None,
                'semantic': {},
                'errors': ['No suitable parser found'],
                'warnings': [],
                'tree_sitter_node': None
            }
            
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            return {
                'success': False,
                'ast': None,
                'semantic': {},
                'errors': [str(e)],
                'warnings': [],
                'tree_sitter_node': None
            }

    def _cleanup(self) -> None:
        """Cleanup parser resources"""
        try:
            for parser in self.parsers:
                if hasattr(parser, 'cleanup'):
                    parser.cleanup()
            self.parsers = []
        except Exception as e:
            logger.error(f"Failed to cleanup parsers: {e}") 