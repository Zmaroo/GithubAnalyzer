from collections.abc import Callable
from typing import Any, cast, List

import pytest
from tree_sitter import Language, Parser, Tree, Node
from tree_sitter_language_pack import (
    SupportedLanguage,
    get_binding,
    get_language,
    get_parser,
    installed_bindings_map,
    get_language_by_extension as ts_get_language_by_extension
)

from src.GithubAnalyzer.core.config.language_config import get_language_by_extension
from src.GithubAnalyzer.core.services.parser_service import ParserService
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_query import TreeSitterQueryHandler

# Get list of installed languages
language_names = sorted(installed_bindings_map.keys())

def test_language_names() -> None:
    """Test language names match installed bindings."""
    supported_languages = sorted([*SupportedLanguage.__args__[0].__args__, *SupportedLanguage.__args__[1].__args__])  # type: ignore[attr-defined]
    installed_languages = sorted(language_names)
    # Check that all installed languages are in the supported languages list
    for lang in installed_languages:
        assert lang in supported_languages, f"Language {lang} is installed but not in supported languages"

@pytest.mark.parametrize("language", language_names)
def test_get_binding(language: SupportedLanguage) -> None:
    """Test getting language binding."""
    binding = get_binding(language)
    assert binding is not None, f"Failed to get binding for {language}"
    assert isinstance(binding, int), "Binding should be an integer pointer"

@pytest.mark.parametrize("language", language_names)
def test_get_language(language: SupportedLanguage) -> None:
    """Test getting language instance."""
    lang = get_language(language)
    assert isinstance(lang, Language), "Should return a tree-sitter Language instance"
    assert lang.version > 0, "Language should have a valid version"

@pytest.mark.parametrize("language", language_names)
def test_get_parser(language: SupportedLanguage) -> None:
    """Test getting parser instance."""
    parser = get_parser(language)
    assert isinstance(parser, Parser), "Should return a tree-sitter Parser instance"
    assert parser.language is not None, "Parser should have a language set"

@pytest.mark.parametrize("handler", [get_language, get_parser])
def test_raises_exception_for_invalid_name(handler: Callable[[str], Any]) -> None:
    with pytest.raises(LookupError):
        handler("invalid")

def test_language_detection():
    """Test language detection."""
    # Test with known extension
    detected = get_language_by_extension(".py")
    assert detected == "python", "Should detect Python for .py files"
    
    # Test with unknown extension
    detected = get_language_by_extension(".unknown")
    assert detected == "unknown", "Should return 'unknown' for unknown extensions"

def test_parser_creation():
    """Test parser creation and basic parsing."""
    parser = get_parser("python")
    assert isinstance(parser, Parser), "Should return a tree-sitter Parser instance"
    
    # Test basic parsing
    tree = parser.parse(b"def test(): pass")
    assert isinstance(tree, Tree), "Should return a tree-sitter Tree instance"
    assert isinstance(tree.root_node, Node), "Should have a valid root node"
    assert tree.root_node.type == "module", "Python code should have a module root"

def test_parser_service():
    """Test parser service with direct tree-sitter types."""
    service = ParserService()
    
    # Test parsing Python code
    result = service.parse_content("def test(): pass", "python")
    assert result.tree is not None, "Should have a parse tree"
    assert isinstance(result.tree, Tree), "Should be a tree-sitter Tree instance"
    assert result.language == "python", "Should preserve language info"
    assert result.is_code, "Should be marked as code"
    
    # Test parsing non-code file
    result = service.parse_file("test.md")
    assert result.tree is None, "Non-code files should have no tree"
    assert result.language == "documentation", "Should identify documentation files"
    assert not result.is_code, "Should be marked as non-code"

def test_query_handler():
    """Test query handler with tree-sitter types."""
    handler = TreeSitterQueryHandler()
    parser = get_parser("python")
    tree = parser.parse(b"def test(): pass")
    
    # Test query creation
    query = handler.create_query("python", "(function_definition name: (identifier) @function.name)")
    assert query is not None, "Should create a valid query"
    
    # Test query execution
    matches = handler.execute_query(query, tree.root_node)
    assert len(matches) == 1, "Should find one function"
    assert matches[0].node.text == b"test", "Should capture function name"

def test_language_pack_integration():
    """Test complete tree-sitter-language-pack integration."""
    # Get language
    lang = get_language("python")
    assert isinstance(lang, Language), "Should get Language instance"
    
    # Create parser
    parser = get_parser("python")
    assert isinstance(parser, Parser), "Should get Parser instance"
    
    # Parse code
    code = "def test(): pass"
    tree = parser.parse(bytes(code, "utf8"))
    assert isinstance(tree, Tree), "Should get Tree instance"
    assert isinstance(tree.root_node, Node), "Should have Node instance"
    assert tree.root_node.type == "module", "Should have correct root type"
    assert not tree.root_node.has_error, "Should parse without errors"
    
    # Test node properties
    func_node = tree.root_node.children[0]
    assert func_node.type == "function_definition", "Should identify function"
    assert func_node.start_point == (0, 0), "Should have correct start"
    assert func_node.end_point == (0, len(code)), "Should have correct end"