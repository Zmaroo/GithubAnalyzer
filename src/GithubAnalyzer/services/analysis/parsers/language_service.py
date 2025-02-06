"""Language service for managing tree-sitter language support."""
import json
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import tree_sitter_c_sharp as tscsharp
from tree_sitter import Language, Node, Parser
from tree_sitter_language_pack import get_binding, get_language, get_parser

from GithubAnalyzer.models.analysis.types import (LanguageId, NodeDict,
                                                  NodeList, QueryPattern,
                                                  QueryResult)
from GithubAnalyzer.models.core.errors import LanguageError, ParserError
from GithubAnalyzer.models.core.language import (EXTENSION_TO_LANGUAGE,
                                                 LANGUAGE_FEATURES,
                                                 SPECIAL_FILENAMES,
                                                 LanguageFeatures,
                                                 LanguageInfo,
                                                 get_base_language)
from GithubAnalyzer.models.core.tree_sitter_core import get_node_text
from GithubAnalyzer.utils.logging import get_logger

from .query_patterns import (EXTENSION_TO_LANGUAGE, QUERY_PATTERNS,
                             SPECIAL_FILENAMES)
from .utils import (TreeSitterServiceBase, get_node_text_safe,
                    get_node_type, is_valid_node, node_to_dict)

from GithubAnalyzer.services.parsers.core.custom_parsers import \
    get_custom_parser

# Initialize logger with correlation ID
logger = get_logger(__name__, correlation_id='language_service')

@dataclass
class LanguageService(TreeSitterServiceBase):
    """Service for managing tree-sitter languages."""
    
    _parsers: Dict[str, Parser] = field(default_factory=dict)
    _patterns: Dict[str, str] = field(default_factory=dict)
    _language_patterns: Dict[str, Dict[str, str]] = field(default_factory=dict)
    _operation_times: Dict[str, float] = field(default_factory=dict)
    _operation_counts: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize language service."""
        super().__post_init__()
        
        self._supported_languages = set(EXTENSION_TO_LANGUAGE.values())
        self._extension_to_language = EXTENSION_TO_LANGUAGE
        
        self._log("debug", "Language service initialized", 
                operation="initialization",
                supported_languages=len(self._supported_languages))
        
        self._initialize_patterns()
        
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
        self._log("debug", "Detecting language for file", 
                operation="language_detection",
                file_path=file_path)
                
        # Handle special filenames without extensions
        filename = Path(file_path).name.lower()
        if filename in SPECIAL_FILENAMES:
            mapped = SPECIAL_FILENAMES[filename]
            if self.is_language_supported(mapped):
                self._log("debug", "Language detected from special filename",
                        operation="language_detection",
                        file_path=file_path,
                        detected_language=mapped)
                return mapped
            return 'plaintext'
        
        # Get extension and try to map it
        extension = Path(file_path).suffix.lstrip('.')
        if not extension:
            # For files without extension, check if we have a custom parser
            custom_parser = get_custom_parser(file_path)
            if custom_parser:
                parser_type = type(custom_parser).__name__
                detected_language = parser_type.replace('Parser', '').lower()
                self._log("debug", "Language detected from custom parser",
                        operation="language_detection",
                        file_path=file_path,
                        parser_type=parser_type,
                        detected_language=detected_language)
                return detected_language
            return 'plaintext'
            
        # Check if extension maps to a language
        if extension.lower() in self._extension_to_language:
            language = self._extension_to_language[extension.lower()]
            if self.is_language_supported(language):
                self._log("debug", "Language detected from file extension",
                        operation="language_detection",
                        file_path=file_path,
                        extension=extension,
                        detected_language=language)
                return language
            
        # For unknown extensions, check if we have a custom parser
        custom_parser = get_custom_parser(file_path)
        if custom_parser:
            parser_type = type(custom_parser).__name__
            detected_language = parser_type.replace('Parser', '').lower()
            self._log("debug", "Language detected from custom parser (unknown extension)",
                    operation="language_detection",
                    file_path=file_path,
                    parser_type=parser_type,
                    detected_language=detected_language)
            return detected_language
                
        self._log("debug", "No language detected, defaulting to plaintext",
                operation="language_detection",
                file_path=file_path)
        return 'plaintext'
        
    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported.
        
        Args:
            language: Language identifier to check
            
        Returns:
            True if the language is supported
        """
        normalized_lang = language.lower().strip()
        if normalized_lang in ['c_sharp', 'c#', 'csharp']:
            return True
        else:
            try:
                from tree_sitter_language_pack import get_language
                lang_obj = get_language(language)
                return lang_obj is not None
            except Exception:
                return False

    def get_tree_sitter_language(self, language: str):
        """
        Return a tree_sitter.Language instance for the given language using the appropriate API.
        
        For 'c_sharp' (and its variants), use the PyPI package tree_sitter_c_sharp with the pypi tree_sitter API.
        For other languages, use the tree_sitter_language_pack API.
        
        Args:
            language (str): The language identifier.
        
        Returns:
            tree_sitter.Language: The corresponding language instance.
        
        Raises:
            LanguageError: If the language cannot be obtained.
        """
        normalized_lang = language.lower().strip()
        if normalized_lang in ['c_sharp', 'c#', 'csharp']:
            import tree_sitter_c_sharp as tscsharp
            from tree_sitter import Language
            return Language(tscsharp.language())
        else:
            try:
                from tree_sitter_language_pack import get_language
                lang_obj = get_language(language)
                if not lang_obj:
                    from GithubAnalyzer.models.core.errors import LanguageError
                    raise LanguageError(f"Failed to obtain language object for {language}.")
                return lang_obj
            except Exception as e:
                from GithubAnalyzer.models.core.errors import LanguageError
                raise LanguageError(f"Error obtaining tree-sitter language for {language}: {str(e)}")

    def get_parser(self, language: str) -> Parser:
        """
        Get a tree-sitter parser for the given language.
        For C# (c_sharp), use the tree-sitter-c-sharp package.
        For all other languages, use tree_sitter_language_pack.
        """
        language_lower = language.lower()
        if language_lower in ['c_sharp', 'c#', 'csharp']:
            import tree_sitter_c_sharp as tscsharp
            from tree_sitter import Language, Parser
            CSHARP_LANGUAGE = Language(tscsharp.language())
            parser = Parser(CSHARP_LANGUAGE)
            return parser
        else:
            from tree_sitter_language_pack import get_parser
            return get_parser(language_lower)

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
            normalized_lang = language.lower().strip()
            if normalized_lang in ['c_sharp', 'c#', 'csharp']:
                lang_obj = self.get_tree_sitter_language(language)
                if not lang_obj:
                    raise LanguageError(f"Failed to get language object for: {language}")
                return lang_obj

            if not self.is_language_supported(language):
                raise LanguageError(f"Language not supported: {language}")

            lang_obj = self.get_tree_sitter_language(language)
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
        code_lines = code.strip().split('\n')
        first_line = code_lines[0].strip() if code_lines else ""

        if first_line.startswith("<?php"):
            return "php"
        if first_line.startswith("<!DOCTYPE html") or first_line.startswith("<html"):
            return "html"
        if first_line.startswith("<?xml"):
            return "xml"
        if first_line.startswith("---") or first_line.startswith("apiVersion:"):
            return "yaml"
        if first_line.startswith("#") and "markdown" in code.lower():
            return "markdown"

        # JavaScript detection
        js_indicators = 0
        js_patterns = [
            r"const\s+\w+\s*=",  # Const declaration
            r"let\s+\w+\s*=",    # Let declaration
            r"var\s+\w+\s*=",    # Var declaration
            r"function\s+\w+\s*\(",  # Function declaration
            r"=>\s*{",           # Arrow function
            r"class\s+\w+\s*{",  # Class declaration
            r"constructor\s*\(",  # Constructor
            r"import\s+.*from",   # Import statement
            r"export\s+",        # Export statement
            r"async\s+function", # Async function
            r"await\s+\w+",     # Await keyword
            r"this\.",          # This reference
            r"new\s+\w+\(",     # New operator
            r"typeof\s+\w+",    # Typeof operator
            r"undefined",       # Undefined value
            r"null",           # Null value
            r"console\.",      # Console methods
            r"document\.",     # DOM manipulation
            r"window\.",       # Window object
            r"prototype\.",    # Prototype
            r"addEventListener", # Event listener
            r"\[\s*\.\.\.",    # Spread operator
            r"Promise\.",      # Promise
            r"async\s*\(",     # Async IIFE
            r"require\(",      # CommonJS require
            r"module\.exports" # CommonJS exports
        ]

        js_keywords = {
            "function", "const", "let", "var", "if", "else", "for", "while",
            "do", "switch", "case", "break", "continue", "return", "try",
            "catch", "finally", "throw", "class", "extends", "new", "this",
            "super", "import", "export", "default", "null", "undefined",
            "typeof", "instanceof", "in", "of", "async", "await", "yield"
        }

        # Check for JavaScript patterns
        for pattern in js_patterns:
            if any(re.search(pattern, line) for line in code_lines):
                js_indicators += 1

        # Check for JavaScript keywords
        code_words = set(re.findall(r'\b\w+\b', code))
        keyword_matches = code_words.intersection(js_keywords)
        js_indicators += len(keyword_matches)

        # Strong indicators of JavaScript
        if js_indicators >= 3:
            return "javascript"

        # Python detection
        python_indicators = 0
        python_patterns = [
            r"def\s+\w+\s*\([^)]*\)\s*:",  # Function definition
            r"class\s+\w+\s*(?:\([^)]*\))?\s*:",  # Class definition
            r"@\w+",  # Decorators
            r"__\w+__",  # Dunder methods/attributes
            r"import\s+\w+",  # Import statements
            r"from\s+[\w.]+\s+import",  # From imports
            r"if\s+__name__\s*==\s*['\"]__main__['\"]",  # Main block
            r":\s*$",  # Line ending with colon
            r"->\s*[\w\[\]]+\s*:",  # Type hints
            r"@dataclass",  # Dataclass decorator
            r"async\s+def",  # Async function
            r"await\s+\w+",  # Await keyword
            r"self\.",  # Self reference
            r"raise\s+\w+",  # Raise statement
            r"except\s+\w+\s+as\s+\w+:",  # Exception handling
            r"with\s+\w+\s+as\s+\w+:",  # Context manager
            r"yield\s+\w+",  # Generator
            r"lambda\s+\w+:",  # Lambda function
            r"def\s+__\w+__\s*\(",  # Special method definition
            r"@property",  # Property decorator
            r"@\w+\.setter",  # Setter decorator
            r"@staticmethod",  # Staticmethod decorator
            r"@classmethod",  # Classmethod decorator
            r"@abstractmethod",  # Abstractmethod decorator
            r"super\(\)\.",  # Super call
            r"pass\s*$",  # Pass statement
            r"None\s*$",  # None value
            r"True\s*$",  # True value
            r"False\s*$",  # False value
            r"print\s*\(",  # Print function
            r"return\s+\w+",  # Return statement
        ]

        python_keywords = {
            "def", "class", "import", "from", "async", "await", 
            "with", "as", "pass", "self", "None", "True", "False",
            "try", "except", "finally", "raise", "yield", "return",
            "and", "or", "not", "is", "in", "lambda", "assert",
            "break", "continue", "del", "elif", "else", "for",
            "global", "if", "while", "nonlocal"
        }

        # Check for Python patterns
        for pattern in python_patterns:
            if any(re.search(pattern, line) for line in code_lines):
                python_indicators += 1

        # Check for Python keywords
        keyword_matches = code_words.intersection(python_keywords)
        python_indicators += len(keyword_matches)

        # Strong indicators of Python
        if python_indicators >= 3:
            return "python"

        # If no strong match found, return plaintext
        return "plaintext"

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

    def parse_content(self, content: str, language: str) -> Optional[Any]:
        """Parse content using tree-sitter.
        
        Args:
            content: Content to parse
            language: Language identifier
            
        Returns:
            Parse tree if successful, None otherwise
            
        Raises:
            LanguageError: If the language is not supported
            ParserError: If parsing fails
        """
        start_time = self._time_operation('parse_content')
        try:
            if not self.is_language_supported(language):
                raise LanguageError(f"Language not supported: {language}")
                
            parser = self.get_parser(language)
            if not parser:
                raise ParserError(f"Failed to get parser for language: {language}")
            
            # Set up logging callback for this parse operation
            def logger_callback(msg: str) -> None:
                self._log("debug", msg, operation="parse", language=language)
            
            # Set the logger for this parse operation
            parser.logger = logger_callback
                
            # Parse the content
            tree = parser.parse(bytes(content, "utf8"))
            if not tree:
                raise ParserError(f"Failed to parse content for language: {language}")
                
            return tree
        except Exception as e:
            self._log("error", f"Error parsing content: {str(e)}")
            return None
        finally:
            # Clean up logger after parsing
            if 'parser' in locals():
                parser.logger = None
            self._end_operation('parse_content', start_time)

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