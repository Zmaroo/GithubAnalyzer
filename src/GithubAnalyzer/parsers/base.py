"""Base parser class"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from ..models import ParseResult

class BaseParser(ABC):
    """Base class for all parsers"""
    
    def __init__(self):
        """Initialize parser"""
        self.current_file: Optional[str] = None
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """Check if file can be parsed"""
        pass
        
    @abstractmethod
    def parse(self, content: str) -> ParseResult:
        """Parse file content"""
        pass
        
    def parse_file(self, file_path: str, content: str) -> ParseResult:
        """Parse file with path context"""
        if not Path(file_path).exists():
            return ParseResult(
                ast=None,
                semantic={},
                errors=[f"File not found: {file_path}"],
                success=False
            )
            
        self.current_file = file_path
        result = self.parse(content)
        self.current_file = None  # Clear after parsing
        return result 