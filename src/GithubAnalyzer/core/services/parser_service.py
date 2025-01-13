"""Parser service for handling file parsing"""
from typing import Dict, Any, Optional, List
from ..parsers.base import BaseParser
from ..parsers.tree_sitter import TreeSitterParser
from ..parsers.custom import (
    ConfigParser,
    DocumentationParser,
    LicenseParser
)
from .base import BaseService

class ParserService(BaseService):
    """Service for parsing files"""
    
    def __init__(self, registry=None):
        """Initialize parser service"""
        super().__init__(registry)
        self.parsers: List[BaseParser] = []
        
    def _initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize parsers"""
        self.parsers = [
            TreeSitterParser(),
            ConfigParser(),
            DocumentationParser(),
            LicenseParser()
        ]
        
    def parse_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Parse file content"""
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser.parse_file(file_path, content)
        return {
            'success': False,
            'errors': ['No suitable parser found']
        } 