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
from .base import BaseService
from ..utils.logging import setup_logger
from ..models.base import ParseResult

logger = setup_logger(__name__)

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
        # Check if file exists first
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
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

    def shutdown(self) -> bool:
        """Cleanup resources"""
        try:
            self.parsers = []
            self.initialized = False
            return True
        except Exception as e:
            logger.error(f"Failed to shutdown parser service: {e}")
            return False 