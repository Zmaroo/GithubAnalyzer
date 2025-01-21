"""Language detection and utilities."""
from typing import Optional, Dict, Any
from pathlib import Path
from tree_sitter import Language, Parser
from tree_sitter_language_pack import get_binding, get_language, get_parser
from src.GithubAnalyzer.core.config.language_config import get_file_type_mapping

class LanguageUtils:
    """Language utilities for Tree-sitter."""

    def __init__(self):
        self.languages: Dict[str, Language] = {}
        self.parsers: Dict[str, Parser] = {}
        self.language_names: Dict[Language, str] = {}

    def initialize_language(self, lang_id: str) -> bool:
        """Initialize a language support.
        
        Args:
            lang_id: Language identifier
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Get language and parser from language pack
            lang = get_language(lang_id)
            parser = get_parser(lang_id)
            
            # Store references
            self.languages[lang_id] = lang
            self.parsers[lang_id] = parser
            self.language_names[lang] = lang_id
            
            return True
            
        except Exception:
            return False

    def detect_language(self, file_path: Path) -> Optional[str]:
        """Detect language from file extension."""
        ext = file_path.suffix.lower()
        return get_file_type_mapping().get(ext)

    def get_parser(self, language: str) -> Optional[Parser]:
        """Get parser for language."""
        return self.parsers.get(language)

    def get_language(self, language: str) -> Optional[Language]:
        """Get language object."""
        return self.languages.get(language)

    def cleanup(self) -> None:
        """Clean up language resources."""
        self.languages.clear()
        self.parsers.clear()
        self.language_names.clear() 