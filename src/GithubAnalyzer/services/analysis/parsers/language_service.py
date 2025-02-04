"""Language service for managing tree-sitter language support."""
import json
import re
from pathlib import Path
from typing import Dict, Optional, Set, Any, List
from tree_sitter import Language, Parser, Node
import time
import threading
from dataclasses import dataclass
import tree_sitter_c_sharp as tscsharp

from tree_sitter_language_pack import get_binding, get_language, get_parser

from GithubAnalyzer.models.analysis.types import (
    LanguageId,
    QueryPattern,
    NodeDict,
    NodeList,
    QueryResult
)
from GithubAnalyzer.models.core.errors import LanguageError, ParserError
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

# Initialize logger
logger = get_logger(__name__)

@dataclass
class LanguageService(TreeSitterServiceBase):
    """Service for managing tree-sitter languages."""
    
    def __post_init__(self):
        """Initialize language service."""
        super().__post_init__()
        self._logger = logger
        self._start_time = time.time()
        
        self._logger.debug("LanguageService initialized", extra={
            'context': {
                'module': 'language',
                'thread': threading.get_ident(),
                'duration_ms': 0
            }
        })
        
        self._supported_languages = set(EXTENSION_TO_LANGUAGE.values())
        self._extension_to_language = EXTENSION_TO_LANGUAGE
        
    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """Get standard context for logging.
        
        Args:
            **kwargs: Additional context key-value pairs
            
        Returns:
            Dict with standard context fields plus any additional fields
        """
        context = {
            'module': 'language',
            'thread': threading.get_ident(),
            'duration_ms': (time.time() - self._start_time) * 1000
        }
        context.update(kwargs)
        return context

    def _log(self, level: str, message: str, **kwargs) -> None:
        """Log with consistent context.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Message to log
            **kwargs: Additional context key-value pairs
        """
        context = self._get_context(**kwargs)
        getattr(self._logger, level)(message, extra={'context': context})

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
        
    def get_tree_sitter_language(self, language: str) -> Language:
        """Return a tree_sitter.Language instance for the given language."""
        if language.lower() in ['c_sharp', 'c#', 'csharp']:
            return Language(tscsharp.language())
        else:
            return Language('build/my-languages.so', language)

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
                
            lang_obj = self.get_tree_sitter_language(language)
            parser = Parser(lang_obj)
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