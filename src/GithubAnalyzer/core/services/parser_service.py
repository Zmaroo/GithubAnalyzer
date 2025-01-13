"""Service for parsing code files"""
from pathlib import Path
from typing import Optional, Dict, Any
from ..parsers.tree_sitter import TreeSitterParser
from ..parsers.custom import DocumentationParser, ConfigParser, LicenseParser
from ..models.base import ParseResult
from .base import BaseService

class ParserService(BaseService):
    """Service for parsing different types of files"""
    
    def __init__(self, registry=None):
        super().__init__()
        self.registry = registry
        self.tree_sitter = TreeSitterParser()
        self.custom_parsers = {
            'documentation': DocumentationParser(),
            'config': ConfigParser(),
            'license': LicenseParser()
        }
        self.file_type_map = {
            '.py': self.tree_sitter,
            '.md': self.custom_parsers['documentation'],
            '.rst': self.custom_parsers['documentation'],
            '.yaml': self.custom_parsers['config'],
            '.yml': self.custom_parsers['config'],
            'LICENSE': self.custom_parsers['license']
        }
        
    def initialize(self) -> bool:
        """Initialize parsers"""
        self.initialized = True
        return True
        
    def shutdown(self) -> bool:
        """Cleanup resources"""
        self.initialized = False
        return True
        
    def parse_file(self, file_path: str, content: str) -> ParseResult:
        """Parse a file using appropriate parser"""
        if not content.strip():
            return ParseResult(
                ast=None,
                semantic={},
                errors=["Empty content"],
                success=False
            )
            
        path = Path(file_path)
        parser = self._get_parser(path)
        
        if not parser:
            return ParseResult(
                ast=None,
                semantic={},
                errors=[f"No parser available for {path.suffix}"],
                success=False
            )
            
        return parser.parse(content)
        
    def _get_parser(self, path: Path):
        """Get appropriate parser for file"""
        if path.name.upper() == 'LICENSE':
            return self.custom_parsers['license']
            
        return self.file_type_map.get(path.suffix.lower()) 