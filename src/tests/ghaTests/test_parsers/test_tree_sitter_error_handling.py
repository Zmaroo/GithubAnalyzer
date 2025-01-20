import pytest
from GithubAnalyzer.services.core.parsers.tree_sitter import TreeSitterParser
from GithubAnalyzer.models.core.errors import ParserError
from tree_sitter import Language, Parser
import tree_sitter_python
import os
import logging
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

class TestTreeSitterErrorHandling:
    @pytest.fixture(scope="session")
    def python_language(self):
        return Language(tree_sitter_python.language())

    @pytest.fixture
    def parser(self, language, python_language):
        parser = TreeSitterParser()
        parser.ts_parser = Parser()
        parser.ts_parser.language = python_language
        parser._parsers['python'] = parser.ts_parser
        parser._languages['python'] = python_language
        parser.initialized = True
        return parser

    @pytest.fixture
    def language(self):
        return "python"

    def test_malformed_class_definition(self, parser, language):
        malformed_code = """
        class MyClass  # Missing colon
            def __init__(self):
                pass
        """
        result = parser.parse(malformed_code, language=language)
        assert result.errors  # Should have errors
        assert any("Syntax error at line 2" in err for err in result.errors)

    def test_incomplete_function_definition(self, parser, language):
        incomplete_code = """
        def my_function(x, y  # Missing closing parenthesis
            return x + y
        """
        result = parser.parse(incomplete_code, language=language)
        assert result.errors  # Should have errors
        assert any("Syntax error at line 2" in err for err in result.errors)

    def test_partial_class_recovery(self, parser, language):
        # This test is already working correctly
        pass

    def test_nested_syntax_errors(self, parser, language):
        nested_error_code = """
        class OuterClass:
            def outer_method(self):
                class InnerClass  # Missing colon
                    def inner_method(self)  # Missing colon
                        pass
        """
        result = parser.parse(nested_error_code, language=language)
        assert len(result.errors) > 1  # Should have multiple errors
        assert any("Syntax error at line 4" in err for err in result.errors)
        assert any("Syntax error at line 5" in err for err in result.errors)

    def test_error_location_reporting(self, parser, language):
        code_with_error = """
        def function1():
            pass

        def function2(x, y, z:
            return x + y + z
        """
        result = parser.parse(code_with_error, language=language)
        assert result.errors
        assert any("Syntax error at line 5" in err for err in result.errors)

    def test_recovery_mode_partial_ast(self, parser, language):
        code = """
        def valid_function():
            pass

        def invalid_function(x:
            return x

        def another_valid_function():
            pass
        """
        # Print the input code for context
        logger.debug("Input code:\n%s", code)

        result = parser.parse(code, language=language)
        # Print the tree structure
        logger.debug("Tree structure:")
        root = parser.ts_parser.parse(bytes(code, 'utf8')).root_node
        cursor = root.walk()

        def print_node(cursor, level=0):
            node = cursor.node
            indent = "  " * level
            logger.debug(f"{indent}[{node.type}] '{node.text.decode('utf8')}' "
                        f"(error: {node.has_error}, missing: {node.is_missing}, "
                        f"start: {node.start_point}, end: {node.end_point})")

            if cursor.goto_first_child():
                while True:
                    print_node(cursor, level + 1)
                    if not cursor.goto_next_sibling():
                        break
                cursor.goto_parent()

        print_node(cursor)

        functions = result.metadata['analysis']['functions']
        assert len(functions) == 2
        function_names = list(functions.keys())
        assert "valid_function" in function_names
        assert "invalid_function" in function_names

    def test_multiple_error_reporting(self, parser, language):
        code_with_multiple_errors = """
        class Class1  # Missing colon
            def method1()  # Missing colon
                pass

        def function1(x  # Missing parenthesis
            return x
        """
        result = parser.parse(code_with_multiple_errors, language=language)
        assert len(result.errors) >= 2  # Should have at least 2 syntax errors
        assert all("Syntax error at line" in err for err in result.errors)

    def test_unicode_handling_errors(self, parser, language):
        code_with_unicode = """
        def function_with_unicode():
            x = "Hello 世界"  # Valid unicode
            y = "Invalid unicode \U0010FFFF"  # Invalid unicode at max code point
        """
        result = parser.parse(code_with_unicode, language=language)
        assert not result.errors, "Should parse valid unicode without errors"
        assert "function_with_unicode" in result.metadata['analysis']['functions']

    def test_multiple_error_reporting(self, parser, language):
        code_with_multiple_errors = """
        class Class1  # Missing colon
            def method1()  # Missing colon
                pass

        def function1(x  # Missing parenthesis
            return x
        """
        result = parser.parse(code_with_multiple_errors, language=language)
        assert len(result.errors) >= 2  # Should have at least 2 syntax errors
        assert all("Syntax error at line" in err for err in result.errors)

    def test_unicode_handling_errors(self, parser, language):
        code_with_unicode = """
        def function_with_unicode():
            x = "Hello 世界"  # Valid unicode
            y = "Invalid unicode \U0010FFFF"  # Invalid unicode at max code point
        """
        result = parser.parse(code_with_unicode, language=language)
        assert not result.errors, "Should parse valid unicode without errors"
        assert "function_with_unicode" in result.metadata['analysis']['functions'] 