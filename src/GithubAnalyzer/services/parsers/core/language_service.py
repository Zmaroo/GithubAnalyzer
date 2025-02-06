"""Language service for managing tree-sitter language support."""
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Set

from tree_sitter import Language, Node, Parser
from tree_sitter_language_pack import get_binding, get_language, get_parser

from GithubAnalyzer.models.core.errors import LanguageError, ParserError
from GithubAnalyzer.models.core.language import (EXTENSION_TO_LANGUAGE,
                                                 LANGUAGE_FEATURES,
                                                 SPECIAL_FILENAMES,
                                                 LanguageFeatures,
                                                 LanguageInfo,
                                                 get_base_language)
from GithubAnalyzer.models.core.tree_sitter_core import get_node_text
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class LanguageService:
    """Service for managing tree-sitter language parsing and queries."""
    
    _parsers: Dict[str, Parser] = field(default_factory=dict)
    _patterns: Dict[str, str] = field(default_factory=dict)
    _language_patterns: Dict[str, Dict[str, str]] = field(default_factory=dict)
    _operation_times: Dict[str, float] = field(default_factory=dict)
    _operation_counts: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize language service."""
        self._log("debug", "Language service initialized")
        self._initialize_patterns()
        
    def _log(self, level: str, message: str, **kwargs):
        """Log with consistent context."""
        getattr(logger, level)(message, extra={'context': kwargs})
        
    def _initialize_patterns(self):
        """Initialize pattern registry."""
        self._patterns = {}
        self._language_patterns = {}
        
    def _time_operation(self, operation: str) -> float:
        """Start timing an operation."""
        if operation not in self._operation_counts:
            self._operation_counts[operation] = 0
        self._operation_counts[operation] += 1
        return time.time()
        
    def _end_operation(self, operation: str, start_time: float):
        """End timing an operation."""
        duration = time.time() - start_time
        if operation not in self._operation_times:
            self._operation_times[operation] = 0
        self._operation_times[operation] += duration
        
        self._log("debug", f"Operation {operation} completed",
                operation=operation,
                duration_ms=duration * 1000,
                count=self._operation_counts[operation],
                total_time_ms=self._operation_times[operation] * 1000)
        
    def get_parser(self, language: str) -> Parser:
        """Get a parser for a language."""
        try:
            # Create parser if needed
            if language not in self._parsers:
                parser = get_parser(language)
                self._parsers[language] = parser
                
                self._log("debug", "Created new parser",
                        language=language)
            
            return self._parsers[language]
            
        except Exception as e:
            self._log("error", "Failed to get parser",
                    language=language,
                    error=str(e))
            raise LanguageError(f"Failed to get parser for language '{language}'") from e

    def get_language_for_file(self, file_path: str) -> str:
        """Get language for a file based on extension."""
        path = Path(file_path)
        ext = path.suffix.lstrip('.')
        filename = path.name.lower()
        
        # Check special filenames first
        if filename in SPECIAL_FILENAMES:
            return SPECIAL_FILENAMES[filename]
            
        # Then check extension
        if ext in EXTENSION_TO_LANGUAGE:
            return EXTENSION_TO_LANGUAGE[ext]
            
        return ""
    
    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported."""
        try:
            return get_language(language) is not None
        except:
            return False
    
    def get_language_features(self, language: str) -> Optional[LanguageFeatures]:
        """Get supported features for a language."""
        return LANGUAGE_FEATURES.get(language)

    def get_language_info(self, language: str) -> Optional[LanguageInfo]:
        """Get information about a language."""
        features = self.get_language_features(language)
        if not features:
            return None
            
        return LanguageInfo(
            name=language,
            features=features,
            is_supported=self.is_language_supported(language)
        )

    def get_tree_sitter_language(self, language: str) -> Optional[Language]:
        """Get tree-sitter Language object for a language."""
        try:
            return get_language(language)
        except Exception as e:
            self._log("error", "Failed to get tree-sitter language",
                    language=language,
                    error=str(e))
            return None

    def parse_content(self, content: str, language: str) -> Optional[Any]:
        """Parse content using tree-sitter."""
        start_time = self._time_operation('parse_content')
        try:
            if not self.is_language_supported(language):
                raise LanguageError(f"Language not supported: {language}")
                
            parser = self.get_parser(language)
            if not parser:
                raise ParserError(f"Failed to get parser for language: {language}")
            
            # Parse the content
            tree = parser.parse(bytes(content, "utf8"))
            if not tree:
                raise ParserError(f"Failed to parse content for language: {language}")
                
            return tree
        except Exception as e:
            self._log("error", f"Error parsing content: {str(e)}")
            return None
        finally:
            self._end_operation('parse_content', start_time)
            
    @property
    def supported_languages(self) -> Set[str]:
        """Get set of supported languages."""
        return {lang for lang in LANGUAGE_FEATURES.keys() if self.is_language_supported(lang)} 