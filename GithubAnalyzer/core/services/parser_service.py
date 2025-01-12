from typing import Dict, Any
from .base_service import BaseService
from ..parsers.tree_sitter import TreeSitterParser
from ..parsers.custom import CustomParserRegistry

class ParserService(BaseService):
    """Centralized parsing service"""
    
    def _initialize(self) -> None:
        self.tree_sitter = TreeSitterParser()
        self.custom_parsers = CustomParserRegistry()
    
    def parse_file(self, file_path: str, content: str) -> ParseResult:
        """Parse file using most appropriate parser"""
        # Try tree-sitter first
        if self.tree_sitter.can_parse(file_path):
            result = self.tree_sitter.parse(content)
            if result.success:
                return result
        
        # Fall back to custom parser
        return self.custom_parsers.parse(file_path, content) 