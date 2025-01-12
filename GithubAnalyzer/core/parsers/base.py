from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ..models.base import ParseResult

class BaseParser(ABC):
    """Base class for all parsers"""
    
    def __init__(self):
        self.current_file = None

    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the file"""
        pass

    @abstractmethod
    def parse(self, content: str) -> ParseResult:
        """Parse content and return results"""
        pass

    def set_current_file(self, filepath: str) -> None:
        """Set the current file being parsed"""
        self.current_file = filepath 