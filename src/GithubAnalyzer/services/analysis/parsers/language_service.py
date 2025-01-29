"""Language service for managing tree-sitter language support."""
import json
from pathlib import Path
from typing import Dict, Optional, Set, Any, List
from tree_sitter import Language, Parser, Node

from tree_sitter_language_pack import get_binding, get_language, get_parser

from GithubAnalyzer.models.analysis.types import (
    LanguageId,
    QueryPattern,
    NodeDict,
    NodeList,
    QueryResult
)
from GithubAnalyzer.models.core.errors import LanguageError
from GithubAnalyzer.utils.logging import get_logger
from .utils import (
    get_node_text,
    node_to_dict,
    is_valid_node,
    get_node_type,
    get_node_text_safe,
    TreeSitterServiceBase
)
from .query_patterns import (
    QUERY_PATTERNS,
    EXTENSION_TO_LANGUAGE,
    SPECIAL_FILENAMES
)

logger = get_logger(__name__)

class LanguageService(TreeSitterServiceBase):
    """Service for managing tree-sitter language operations."""
    
    def __init__(self):
        """Initialize the language service."""
        super().__init__()
        self._supported_languages = set(EXTENSION_TO_LANGUAGE.values())
        self._extension_to_language = EXTENSION_TO_LANGUAGE
        
    @property
    def supported_languages(self) -> Set[str]:
        """Get the set of supported languages."""
        return self._supported_languages
        
    @property
    def extension_to_language(self) -> dict:
        """Get the mapping of file extensions to language identifiers."""
        return self._extension_to_language
        
    def get_language_for_file(self, file_path: str) -> str:
        """Get the language identifier for a file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language identifier string. Returns 'plaintext' for unsupported or unknown file types.
        """
        # Handle special filenames without extensions
        filename = Path(file_path).name.lower()
        if filename in SPECIAL_FILENAMES:
            mapped = SPECIAL_FILENAMES[filename]
            if self.is_language_supported(mapped):
                return mapped
            return 'plaintext'
        
        # Get extension and try to map it
        extension = Path(file_path).suffix.lstrip('.')
        if not extension:
            # Try to detect language from content for files without extension
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                detected = self.detect_language(content)
                if detected != 'plaintext':
                    return detected
            except:
                pass
            return 'plaintext'
            
        # Check if extension maps to a language
        if extension.lower() in self._extension_to_language:
            language = self._extension_to_language[extension.lower()]
            if self.is_language_supported(language):
                return language
                
        # Try to detect language from content for unknown extensions
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            detected = self.detect_language(content)
            if detected != 'plaintext':
                return detected
        except:
            pass
            
        return 'plaintext'
        
    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported.
        
        Args:
            language: Language identifier to check
            
        Returns:
            True if the language is supported
        """
        try:
            # Try to get the language object - if it succeeds, the language is supported
            return bool(get_language(language))
        except:
            return False
        
    def get_parser(self, language: str) -> Parser:
        """Get a parser for a language.
        
        Args:
            language: Language identifier
            
        Returns:
            Configured Parser instance
            
        Raises:
            LanguageError: If the language is not supported or parser creation fails
        """
        start_time = self._time_operation('get_parser')
        try:
            if not self.is_language_supported(language):
                raise LanguageError(f"Language not supported: {language}")
                
            parser = get_parser(language)
            if not parser:
                raise LanguageError(f"Failed to create parser for language: {language}")
            return parser
        except Exception as e:
            raise LanguageError(f"Error creating parser for {language}: {str(e)}")
        finally:
            self._end_operation('get_parser', start_time)
            
    def get_language_object(self, language: str) -> Language:
        """Get the tree-sitter Language object for a language.
        
        Args:
            language: Language identifier
            
        Returns:
            Language object
            
        Raises:
            LanguageError: If the language is not supported or object creation fails
        """
        start_time = self._time_operation('get_language_object')
        try:
            if not self.is_language_supported(language):
                raise LanguageError(f"Language not supported: {language}")
                
            lang_obj = get_language(language)
            if not lang_obj:
                raise LanguageError(f"Failed to get language object for: {language}")
            return lang_obj
        except Exception as e:
            raise LanguageError(f"Error getting language object for {language}: {str(e)}")
        finally:
            self._end_operation('get_language_object', start_time)

    def detect_language(self, code: str) -> str:
        """Detect the programming language of a code snippet.

        Args:
            code: The code snippet to analyze.

        Returns:
            The detected language identifier.
        """
        if not code or code.isspace():
            return "plaintext"

        # Special case handling for common file patterns
        if code.strip().startswith("<?php"):
            return "php"
        if code.strip().startswith("<!DOCTYPE html") or code.strip().startswith("<html"):
            return "html"
        if code.strip().startswith("<?xml"):
            return "xml"
        if code.strip().startswith("---") or code.strip().startswith("apiVersion:"):
            return "yaml"
        if code.strip().startswith("#") and "markdown" in code.lower():
            return "markdown"

        # Define language features for better detection
        language_features = {
            "python": {
                "keywords": ["def", "class", "import", "from", "async", "await", "with", "as", "pass"],
                "patterns": [
                    r"def\s+\w+\s*\([^)]*\)\s*:",
                    r"class\s+\w+\s*(?:\([^)]*\))?\s*:",
                    r"@\w+",
                    r"__\w+__"
                ]
            },
            "javascript": {
                "keywords": ["const", "let", "var", "function", "class", "extends", "async", "await"],
                "patterns": [
                    r"const\s+\w+\s*=",
                    r"let\s+\w+\s*=",
                    r"function\s*\w*\s*\([^)]*\)\s*{",
                    r"class\s+\w+\s*{",
                    r"=>\s*{",
                    r"export\s+(?:default\s+)?(?:class|function|const|let)"
                ]
            },
            "typescript": {
                "keywords": ["interface", "type", "enum", "namespace", "implements", "extends"],
                "patterns": [
                    r"interface\s+\w+\s*{",
                    r"type\s+\w+\s*=",
                    r":\s*(?:string|number|boolean|any|void)\s*[;,)]",
                    r"<[^>]+>"
                ]
            },
            "rust": {
                "keywords": ["fn", "pub", "struct", "impl", "trait", "let", "mut", "match"],
                "patterns": [
                    r"fn\s+\w+\s*(?:<[^>]+>)?\s*\([^)]*\)\s*(?:->\s*\w+\s*)?{",
                    r"pub\s+(?:fn|struct|trait)",
                    r"let\s+mut\s+\w+",
                    r"::\w+",
                    r"Result<\w+,\s*\w+>"
                ]
            },
            "go": {
                "keywords": ["func", "package", "import", "type", "struct", "interface", "var", "const"],
                "patterns": [
                    r"package\s+\w+",
                    r"func\s+\w+\s*\([^)]*\)\s*(?:\([^)]*\))?\s*{",
                    r"type\s+\w+\s+struct\s*{",
                    r"var\s+\w+\s+\w+"
                ]
            },
            "java": {
                "keywords": ["public", "private", "protected", "class", "interface", "extends", "implements"],
                "patterns": [
                    r"public\s+class\s+\w+",
                    r"private\s+\w+\s+\w+\s*\([^)]*\)",
                    r"System\.",
                    r"@Override"
                ]
            }
        }

        # Calculate scores for each language
        scores = {}
        for lang, features in language_features.items():
            score = 0
            
            # Check for keywords
            for keyword in features["keywords"]:
                if keyword in code:
                    score += 1
                    
            # Check for patterns
            import re
            for pattern in features["patterns"]:
                matches = re.findall(pattern, code)
                score += len(matches) * 2  # Patterns are weighted more heavily
                
            # Try parsing with tree-sitter
            try:
                parser = self.get_parser(lang)
                tree = parser.parse(bytes(code, "utf8"))
                error_count = len(list(self._find_error_nodes(tree.root_node)))
                total_nodes = len(list(tree.root_node.walk()))
                
                if total_nodes > 0:
                    error_ratio = error_count / total_nodes
                    if error_ratio < 0.3:  # Less than 30% error nodes
                        score += 5  # Significant boost for successful parsing
                        if error_ratio < 0.1:  # Less than 10% error nodes
                            score += 5  # Additional boost for very clean parsing
            except Exception:
                continue
            
            if score > 0:
                scores[lang] = score
                
        if scores:
            best_lang = max(scores.items(), key=lambda x: x[1])[0]
            return best_lang
            
        return "plaintext"  # Default to plaintext if no language is detected

    def _find_error_nodes(self, node: Node) -> List[Node]:
        """Find all error nodes in a tree."""
        errors = []
        if node.has_error:
            errors.append(node)
        for child in node.children:
            errors.extend(self._find_error_nodes(child))
        return errors

    def get_binding(self, language: str) -> int:
        """Get language binding using tree-sitter-language-pack.
        
        Args:
            language: Language identifier
            
        Returns:
            Language binding ID
            
        Raises:
            LanguageError: If language is not supported or binding retrieval fails
        """
        start_time = self._time_operation('get_binding')
        try:
            try:
                return get_binding(language)
            except LookupError as e:
                raise LanguageError(f"Language {language} is not supported: {str(e)}")
            except Exception as e:
                raise LanguageError(f"Failed to get binding for {language}: {str(e)}")
        finally:
            self._end_operation('get_binding', start_time) 