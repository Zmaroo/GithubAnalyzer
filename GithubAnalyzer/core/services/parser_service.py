from typing import Dict, Any, Optional
from pathlib import Path
from .base_service import BaseService
from ..parsers.tree_sitter import TreeSitterParser
from ..parsers.custom import (
    ConfigParser,
    DocumentationParser,
    LicenseParser
)
from ..models.base import ParseResult
from ..utils.logging import setup_logger

logger = setup_logger(__name__)

class ParserService(BaseService):
    """Centralized parsing service"""
    
    def _initialize(self) -> None:
        # Initialize parsers
        self.tree_sitter = TreeSitterParser()
        self.custom_parsers = {
            'config': ConfigParser(),
            'documentation': DocumentationParser(),
            'license': LicenseParser()
        }
        
        # File type mappings
        self.file_type_map = {
            # Config files
            '.json': 'config',
            '.yaml': 'config',
            '.yml': 'config',
            '.toml': 'config',
            '.ini': 'config',
            'pyproject.toml': 'config',
            'setup.cfg': 'config',
            
            # Documentation files
            '.md': 'documentation',
            '.rst': 'documentation',
            '.txt': 'documentation',
            'README': 'documentation',
            'CHANGELOG': 'documentation',
            
            # License files
            'LICENSE': 'license',
            'COPYING': 'license'
        }
    
    def parse_file(self, file_path: str, content: str) -> ParseResult:
        """Parse file using most appropriate parser"""
        try:
            path = Path(file_path)
            
            # Try tree-sitter first for code files
            if self.tree_sitter.can_parse(file_path):
                result = self.tree_sitter.parse(content)
                if result.success:
                    return result
                logger.warning(f"Tree-sitter parse failed for {file_path}, trying custom parser")
            
            # Use custom parser based on file type
            parser_type = self._get_parser_type(path)
            if parser_type and parser_type in self.custom_parsers:
                parser = self.custom_parsers[parser_type]
                parser.set_current_file(file_path)
                return parser.parse(content)
            
            # Return error if no parser available
            return ParseResult(
                ast=None,
                semantic={},
                errors=[f"No parser available for {file_path}"],
                success=False
            )
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return ParseResult(
                ast=None,
                semantic={},
                errors=[str(e)],
                success=False
            )

    def _get_parser_type(self, path: Path) -> Optional[str]:
        """Determine appropriate parser type for file"""
        # Check exact filename matches first
        if path.name in self.file_type_map:
            return self.file_type_map[path.name]
            
        # Then check extensions
        if path.suffix in self.file_type_map:
            return self.file_type_map[path.suffix]
            
        # Special cases for documentation
        if path.name.upper() in ['README', 'CHANGELOG', 'CONTRIBUTING']:
            return 'documentation'
            
        return None

    def get_available_parsers(self) -> Dict[str, Any]:
        """Get information about available parsers"""
        return {
            'tree_sitter': {
                'available': bool(self.tree_sitter),
                'supported_languages': self.tree_sitter.supported_languages if self.tree_sitter else []
            },
            'custom_parsers': {
                name: parser.__class__.__name__
                for name, parser in self.custom_parsers.items()
            }
        } 