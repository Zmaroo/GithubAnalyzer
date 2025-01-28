"""Language service for managing tree-sitter language support."""
import json
from pathlib import Path
from typing import Dict, Optional, Set, Any, Callable, List, Union
from tree_sitter import Parser, Language
from tree_sitter_language_pack import get_binding, get_language, get_parser

class CustomParser:
    """Base class for custom parsers for unsupported languages."""
    def parse(self, content: bytes) -> Any:
        """Parse content into an AST-like structure."""
        raise NotImplementedError()
        
    def query(self, node: Any, pattern: str) -> List[Dict[str, Any]]:
        """Query the AST-like structure."""
        raise NotImplementedError()

class LanguageService:
    """Service for managing tree-sitter language support."""
    
    def __init__(self):
        """Initialize language service."""
        self._language_definitions = self._load_language_definitions()
        self._supported_languages = self._get_supported_languages()
        self._extension_map = self._build_extension_map()
        self._custom_parsers: Dict[str, CustomParser] = {}
        
    def _load_language_definitions(self) -> Dict:
        """Load language definitions from JSON."""
        definitions_path = Path(__file__).parent.parent.parent.parent.parent / "docs" / "language_definitions.json"
        with open(definitions_path) as f:
            return json.load(f)
            
    def _get_supported_languages(self) -> Set[str]:
        """Get set of languages supported by tree-sitter-language-pack."""
        supported = set()
        for lang in self._language_definitions.keys():
            try:
                # Try to get language from pack
                get_language(lang)
                supported.add(lang)
            except Exception:
                continue
        return supported
        
    def _build_extension_map(self) -> Dict[str, str]:
        """Build mapping of file extensions to language identifiers."""
        return {
            # C family
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.hpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c++': 'cpp',
            
            # Web
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.php': 'php',
            
            # System
            '.sh': 'bash',
            '.bash': 'bash',
            '.rs': 'rust',
            '.go': 'go',
            '.java': 'java',
            '.scala': 'scala',
            '.rb': 'ruby',
            '.py': 'python',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.kts': 'kotlin',
            
            # Data/Config
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.xml': 'xml',
            
            # Documentation
            '.md': 'markdown',
            '.rst': 'rst',
            '.org': 'org',
            
            # Other languages
            '.lua': 'lua',
            '.r': 'r',
            '.elm': 'elm',
            '.ex': 'elixir',
            '.exs': 'elixir',
            '.erl': 'erlang',
            '.hrl': 'erlang',
            '.hs': 'haskell',
            '.lhs': 'haskell',
            '.pl': 'perl',
            '.pm': 'perl',
            '.sql': 'sql',
            '.vue': 'vue',
            '.zig': 'zig'
        }
        
    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported by tree-sitter-language-pack."""
        return language in self._supported_languages
        
    def get_language_for_file(self, file_path: str) -> Optional[str]:
        """Get language identifier for a file path."""
        ext = Path(file_path).suffix.lower()
        return self._extension_map.get(ext)
        
    def register_custom_parser(self, language: str, parser: CustomParser) -> None:
        """Register a custom parser for an unsupported language.
        
        Args:
            language: Language identifier
            parser: Custom parser implementation
        """
        if language in self._supported_languages:
            raise ValueError(f"Language {language} is already supported by tree-sitter-language-pack")
        self._custom_parsers[language] = parser
        
    def get_parser(self, language: str) -> Union[Parser, CustomParser]:
        """Get parser for a language, with fallback to custom parser.
        
        Args:
            language: Language identifier
            
        Returns:
            Tree-sitter parser or custom parser
            
        Raises:
            ValueError: If language is not supported and no custom parser exists
        """
        try:
            if self.is_language_supported(language):
                return get_parser(language)
            if language in self._custom_parsers:
                return self._custom_parsers[language]
            raise ValueError(f"Language {language} is not supported and no custom parser exists")
        except Exception as e:
            if language in self._custom_parsers:
                return self._custom_parsers[language]
            raise ValueError(f"Failed to get parser for {language}: {str(e)}")
            
    def get_query_methods(self, language: str) -> Dict[str, Callable]:
        """Get language-specific query methods.
        
        Args:
            language: Language identifier
            
        Returns:
            Dictionary mapping query types to query methods
        """
        if language in self._custom_parsers:
            # Custom parsers should implement their own query methods
            parser = self._custom_parsers[language]
            return {
                'query': parser.query
            }
            
        # Get tree-sitter query methods based on language
        methods = {
            'find_functions': self._get_function_query(language),
            'find_classes': self._get_class_query(language),
            'find_methods': self._get_method_query(language),
            'find_imports': self._get_import_query(language),
            'find_variables': self._get_variable_query(language)
        }
        
        # Add language-specific query methods
        if language == 'python':
            methods.update({
                'find_decorators': self._get_python_decorator_query(),
                'find_async_functions': self._get_python_async_query()
            })
        elif language in {'javascript', 'typescript'}:
            methods.update({
                'find_jsx_elements': self._get_js_jsx_query(),
                'find_exports': self._get_js_export_query()
            })
        elif language == 'rust':
            methods.update({
                'find_traits': self._get_rust_trait_query(),
                'find_impls': self._get_rust_impl_query()
            })
            
        return methods
        
    def _get_function_query(self, language: str) -> Callable:
        """Get function query method for a language."""
        query_pattern = self._get_query_pattern(language, 'function')
        def query_func(node: Any) -> List[Dict[str, Any]]:
            return self._execute_query(node, query_pattern)
        return query_func
        
    def _get_class_query(self, language: str) -> Callable:
        """Get class query method for a language."""
        query_pattern = self._get_query_pattern(language, 'class')
        def query_func(node: Any) -> List[Dict[str, Any]]:
            return self._execute_query(node, query_pattern)
        return query_func
        
    def _get_method_query(self, language: str) -> Callable:
        """Get method query method for a language."""
        query_pattern = self._get_query_pattern(language, 'method')
        def query_func(node: Any) -> List[Dict[str, Any]]:
            return self._execute_query(node, query_pattern)
        return query_func
        
    def _get_import_query(self, language: str) -> Callable:
        """Get import query method for a language."""
        query_pattern = self._get_query_pattern(language, 'import')
        def query_func(node: Any) -> List[Dict[str, Any]]:
            return self._execute_query(node, query_pattern)
        return query_func
        
    def _get_variable_query(self, language: str) -> Callable:
        """Get variable query method for a language."""
        query_pattern = self._get_query_pattern(language, 'variable')
        def query_func(node: Any) -> List[Dict[str, Any]]:
            return self._execute_query(node, query_pattern)
        return query_func
        
    # Language-specific query methods
    def _get_python_decorator_query(self) -> Callable:
        """Get Python decorator query method."""
        query_pattern = """
            (decorator
              name: (_) @decorator.name
              arguments: (argument_list)? @decorator.args) @decorator
        """
        def query_func(node: Any) -> List[Dict[str, Any]]:
            return self._execute_query(node, query_pattern)
        return query_func
        
    def _get_python_async_query(self) -> Callable:
        """Get Python async function query method."""
        query_pattern = """
            (async_function_definition
              name: (identifier) @async.name
              parameters: (parameters) @async.params
              body: (block) @async.body) @async.def
        """
        def query_func(node: Any) -> List[Dict[str, Any]]:
            return self._execute_query(node, query_pattern)
        return query_func
        
    def _get_js_jsx_query(self) -> Callable:
        """Get JSX element query method."""
        query_pattern = """
            (jsx_element
              opening_element: (jsx_opening_element
                name: (_) @jsx.tag.name
                attributes: (jsx_attributes)? @jsx.attrs)
              children: (_)* @jsx.children) @jsx
        """
        def query_func(node: Any) -> List[Dict[str, Any]]:
            return self._execute_query(node, query_pattern)
        return query_func
        
    def _get_js_export_query(self) -> Callable:
        """Get JavaScript/TypeScript export query method."""
        query_pattern = """
            (export_statement
              declaration: (_) @export.declaration) @export
        """
        def query_func(node: Any) -> List[Dict[str, Any]]:
            return self._execute_query(node, query_pattern)
        return query_func
        
    def _get_rust_trait_query(self) -> Callable:
        """Get Rust trait query method."""
        query_pattern = """
            (trait_item
              name: (type_identifier) @trait.name
              body: (declaration_list) @trait.body) @trait
        """
        def query_func(node: Any) -> List[Dict[str, Any]]:
            return self._execute_query(node, query_pattern)
        return query_func
        
    def _get_rust_impl_query(self) -> Callable:
        """Get Rust impl query method."""
        query_pattern = """
            (impl_item
              type: (type_identifier) @impl.type
              trait: (type_identifier)? @impl.trait
              body: (declaration_list) @impl.body) @impl
        """
        def query_func(node: Any) -> List[Dict[str, Any]]:
            return self._execute_query(node, query_pattern)
        return query_func
        
    def _execute_query(self, node: Any, query_pattern: str) -> List[Dict[str, Any]]:
        """Execute a query pattern on a node."""
        if isinstance(node, (dict, CustomParser)):
            # Handle custom parser nodes
            parser = self._custom_parsers.get(node.get('language'))
            if parser:
                return parser.query(node, query_pattern)
            return []
            
        try:
            # Handle tree-sitter nodes
            lang = node.tree.language
            query = Query(lang, query_pattern)
            matches = []
            for _, match in query.matches(node):
                matches.append(match)
            return matches
        except Exception:
            return []
            
    def _get_query_pattern(self, language: str, pattern_type: str) -> str:
        """Get query pattern for a language and type."""
        from .query_patterns import get_query_pattern
        return get_query_pattern(language, pattern_type)
        
    def get_language(self, language: str):
        """Get language object, with error handling."""
        if not self.is_language_supported(language):
            raise ValueError(f"Language {language} is not supported by tree-sitter-language-pack")
        return get_language(language)
        
    def get_binding(self, language: str) -> int:
        """Get language binding, with error handling."""
        if not self.is_language_supported(language):
            raise ValueError(f"Language {language} is not supported by tree-sitter-language-pack")
        return get_binding(language)
        
    def get_language_map(self) -> Dict[str, str]:
        """Get mapping of language identifiers to tree-sitter language names."""
        # For now, we use a 1:1 mapping since tree-sitter-language-pack uses the same names
        return {lang: lang for lang in self._supported_languages}
        
    @property
    def supported_languages(self) -> Set[str]:
        """Get set of supported languages."""
        return self._supported_languages.copy()
        
    @property
    def extension_map(self) -> Dict[str, str]:
        """Get copy of extension map."""
        return self._extension_map.copy() 