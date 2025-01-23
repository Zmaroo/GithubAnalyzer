"""Tests for tree-sitter editor functionality."""
import pytest
from pathlib import Path
from unittest.mock import Mock
from tree_sitter import Parser, Point, Tree, Query, Range, Node
from tree_sitter_language_pack import get_binding, get_language, get_parser

from src.GithubAnalyzer.core.models.errors import ParserError
from src.GithubAnalyzer.core.utils.logging import get_logger
from src.GithubAnalyzer.analysis.services.parsers.tree_sitter_editor import (
    TreeSitterEditor, 
    EditOperation,
    TreeSitterLogHandler
)
import logging

logger = get_logger(__name__)

@pytest.fixture
def editor():
    """Create a TreeSitterEditor instance."""
    return TreeSitterEditor()

@pytest.fixture
def python_language():
    """Get the Python language for tree-sitter."""
    return get_language('python')

@pytest.fixture
def python_parser(python_language):
    """Create a Python parser using tree-sitter."""
    parser = get_parser('python')
    assert parser.language == python_language
    return parser

@pytest.fixture
def python_query(python_language):
    """Create a query for Python code."""
    query_string = """
    (function_definition
      name: (identifier) @function.name
      parameters: (parameters) @function.params
      body: (block) @function.body)
    """
    return Query(python_language, query_string)

@pytest.fixture
def temp_dot_file(tmp_path):
    """Create a temporary file for DOT graph output."""
    return tmp_path / "tree.dot"

def test_cache_operations(editor, python_parser):
    """Test tree caching operations."""
    # Initial parse
    code = "def hello(): pass"
    source_bytes = bytes(code, "utf8")
    tree = python_parser.parse(source_bytes)
    
    # Test caching
    editor.cache_tree("test.py", tree, source_bytes)
    
    # Get cached tree and verify
    cached = editor.get_cached_tree("test.py")
    assert cached is not None
    
    # Get cached source and verify
    cached_source = editor.get_source_bytes("test.py")
    assert cached_source is not None
    assert cached_source == source_bytes
    
    # Test getting non-existent cache
    assert editor.get_cached_tree("nonexistent.py") is None

def test_backup_and_restore(editor, python_parser):
    """Test tree backup and restoration."""
    # Initial parse
    code = "def hello(): pass"
    source_bytes = bytes(code, "utf8")
    tree = python_parser.parse(source_bytes)
    
    # Cache and backup
    editor.cache_tree("test.py", tree, source_bytes)
    editor.backup_tree("test.py")
    
    # Create new code and parse
    new_code = "def world(): return True"
    new_source = bytes(new_code, "utf8")
    new_tree = python_parser.parse(new_source)
    
    # Cache the new tree
    editor.cache_tree("test.py", new_tree, new_source)
    
    # Restore from backup
    assert editor.restore_tree("test.py", python_parser)
    
    # Get restored tree and verify by reparsing
    restored_source = editor.get_source_bytes("test.py")
    assert restored_source is not None
    
    # Verify by reparsing with the restored source
    python_parser.reset()
    verified_tree = python_parser.parse(restored_source)
    assert verified_tree is not None
    # Compare the source bytes directly instead of accessing root_node.text
    assert restored_source == source_bytes

def test_is_valid_position(editor, python_parser):
    """Test position validation."""
    code = "def hello(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    
    # Valid positions
    assert editor.is_valid_position(tree, Point(0, 0))  # Start
    assert editor.is_valid_position(tree, Point(0, 4))  # 'hello'
    assert editor.is_valid_position(tree, Point(0, len(code)))  # End
    
    # Invalid positions
    assert not editor.is_valid_position(tree, Point(-1, 0))  # Before start
    assert not editor.is_valid_position(tree, Point(0, -1))  # Before start
    assert not editor.is_valid_position(tree, Point(1, 0))   # After end
    assert not editor.is_valid_position(tree, Point(0, len(code) + 1))  # After end

def test_create_edit_operation(editor, python_parser):
    """Test creating edit operations."""
    tree = python_parser.parse(bytes("def hello(): pass", "utf8"))
    
    # Replace 'pass' with 'return True'
    edit = editor.create_edit_operation(
        tree=tree,
        old_text="pass",
        new_text="return True",
        start_position=Point(0, 12)
    )
    
    assert edit.start_byte == 12
    assert edit.old_end_byte == 16  # 'pass' is 4 bytes
    assert edit.new_end_byte == 23  # 'return True' is 11 bytes
    assert edit.start_point == Point(0, 12)
    assert edit.old_end_point == Point(0, 16)
    assert edit.new_end_point == Point(0, 23)
    assert edit.new_text == "return True"

def test_apply_edit(editor, python_parser):
    """Test applying an edit to a tree."""
    tree = python_parser.parse(bytes("def hello(): pass", "utf8"))
    
    # Create and apply edit
    edit = editor.create_edit_operation(
        tree=tree,
        old_text="pass",
        new_text="return True",
        start_position=Point(0, 12)
    )
    
    editor.apply_edit(tree, edit)
    assert tree.root_node.has_changes
    
    # Test invalid position
    with pytest.raises(ParserError):
        invalid_edit = editor.create_edit_operation(
            tree=tree,
            old_text="pass",
            new_text="return True",
            start_position=Point(100, 0)  # Invalid position
        )
        editor.apply_edit(tree, invalid_edit)

def test_reparse_tree(editor, python_parser):
    """Test reparsing a tree after edits."""
    # Initial parse
    old_code = "def hello(): pass"
    old_source = bytes(old_code, "utf8")
    old_tree = python_parser.parse(old_source)
    
    # Create and apply edit
    edit = editor.create_edit_operation(
        tree=old_tree,
        old_text="pass",
        new_text="return True",
        start_position=Point(0, 12)
    )
    editor.apply_edit(tree=old_tree, edit=edit)
    
    # Reparse with new code
    new_code = "def hello(): return True"
    new_source = bytes(new_code, "utf8")
    python_parser.reset()
    new_tree = python_parser.parse(new_source, old_tree)
    
    assert new_tree is not None
    # Verify by reparsing with new source
    python_parser.reset()
    verified_tree = python_parser.parse(new_source)
    assert verified_tree is not None
    assert verified_tree.root_node.text == new_source
    
    # Test reparsing invalid code
    with pytest.raises(ParserError):
        invalid_edit = editor.create_edit_operation(
            tree=new_tree,
            old_text="return True",
            new_text="return",  # Invalid - missing expression
            start_position=Point(0, 12)
        )
        editor.apply_edit(tree=new_tree, edit=invalid_edit)

def test_verify_tree_changes(editor, python_parser):
    """Test verifying tree changes."""
    # Parse valid code
    valid_code = "def hello(): pass"
    valid_source = bytes(valid_code, "utf8")
    tree = python_parser.parse(valid_source)
    
    # Valid tree should pass verification
    assert editor.verify_tree_changes(tree)
    
    # Parse invalid code
    invalid_code = "{"
    invalid_source = bytes(invalid_code, "utf8")
    python_parser.reset()
    invalid_tree = python_parser.parse(invalid_source)
    
    # Invalid tree should fail verification
    assert not editor.verify_tree_changes(invalid_tree)

def test_update_tree(editor, python_parser):
    """Test updating a tree with multiple edits."""
    code = "def hello(): pass"
    file_path = "test.py"
    
    # Initial parse
    tree = python_parser.parse(bytes(code, "utf8"))
    editor.cache_tree(file_path, tree)
    
    # Create edits
    edits = [
        editor.create_edit_operation(
            tree=tree,
            old_text="hello",
            new_text="world",
            start_position=Point(0, 4)
        ),
        editor.create_edit_operation(
            tree=tree,
            old_text="pass",
            new_text="return True",
            start_position=Point(0, 12)
        )
    ]
    
    # Apply updates
    updated_tree = editor.update_tree(file_path, edits, python_parser)
    assert updated_tree is not None
    assert updated_tree.root_node.text.decode('utf8') == "def world(): return True"

def test_get_changed_ranges(editor, python_parser):
    """Test getting changed ranges between trees."""
    old_code = "def hello(): pass"
    new_code = "def hello(): return True"
    
    old_tree = python_parser.parse(bytes(old_code, "utf8"))
    new_tree = python_parser.parse(bytes(new_code, "utf8"))
    
    ranges = editor.get_changed_ranges(old_tree, new_tree)
    assert len(ranges) > 0  # Should detect the change
    
    # Test with identical trees
    same_ranges = editor.get_changed_ranges(old_tree, old_tree)
    assert len(same_ranges) == 0  # No changes

def test_visualize_tree(editor, python_parser, temp_dot_file):
    """Test tree visualization."""
    code = "def hello(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    
    # Generate DOT graph
    assert editor.visualize_tree(tree, temp_dot_file)
    assert temp_dot_file.exists()
    assert temp_dot_file.stat().st_size > 0
    
    # Test with invalid path
    assert not editor.visualize_tree(tree, "/nonexistent/path/tree.dot")

def test_get_tree_with_offset(editor, python_parser):
    """Test getting tree with offset."""
    code = "def hello(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    
    # Get tree with offset
    offset_bytes = 4  # Skip "def "
    offset_extent = (0, 4)  # Row 0, Column 4
    root_with_offset = editor.get_tree_with_offset(tree, offset_bytes, offset_extent)
    
    assert root_with_offset is not None
    # Verify offset was applied
    assert root_with_offset.start_byte == tree.root_node.start_byte + offset_bytes
    assert root_with_offset.start_point[1] == tree.root_node.start_point[1] + offset_extent[1]
    
    # Test with invalid offset
    assert editor.get_tree_with_offset(None, -1, (-1, -1)) is None

def test_restore_tree_logs_error(editor, python_parser, caplog):
    """Test that restore_tree logs errors."""
    caplog.set_level(logging.ERROR)
    
    # Try to restore non-existent backup
    editor.restore_tree("nonexistent.py", python_parser)
    
    # Check log message
    assert any("Failed to restore tree from backup" in record.message 
              for record in caplog.records)

def test_get_changed_ranges_logs_error(editor, python_parser, caplog):
    """Test that get_changed_ranges logs errors."""
    # Try to get changes with invalid trees
    editor.get_changed_ranges(None, None)
    assert "Failed to get changed ranges" in caplog.text

def test_visualize_tree_logs_error(editor, python_parser, caplog):
    """Test that visualize_tree logs errors."""
    code = "def hello(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    
    # Try to write to invalid path
    editor.visualize_tree(tree, "/nonexistent/path/tree.dot")
    assert "Failed to write DOT graph" in caplog.text

def test_get_tree_with_offset_logs_error(editor, python_parser, caplog):
    """Test that get_tree_with_offset logs errors."""
    caplog.set_level(logging.ERROR)
    code = "def hello(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    
    # Try with invalid offset
    editor.get_tree_with_offset(None, -1, (-1, -1))
    assert "Failed to get tree with offset" in caplog.text

def test_update_tree_logs_warning_on_validation_failure(editor, python_parser, caplog):
    """Test that update_tree logs warning on validation failure."""
    caplog.set_level(logging.WARNING)
    code = "def hello(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    editor.cache_tree("test.py", tree)
    editor.backup_tree("test.py")
    
    # Create an edit that will cause validation to fail
    edit = EditOperation(
        start_byte=0,
        old_end_byte=1,
        new_end_byte=1,
        start_point=Point(0, 0),
        old_end_point=Point(0, 1),
        new_end_point=Point(0, 1),
        new_text="{"  # Invalid Python syntax
    )
    
    editor.update_tree("test.py", [edit], python_parser)
    
    # Check log message
    assert any("Tree validation failed" in record.message 
              for record in caplog.records)

def test_backup_restore_with_invalid_source(editor, python_parser, caplog):
    """Test tree restoration with invalid source code."""
    # Setup valid tree and backup
    code = "def hello(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    editor.cache_tree("test.py", tree)
    editor.backup_tree("test.py")
    
    # Corrupt the backup
    editor._tree_backups["test.py"] = b"invalid python code {{{{"
    
    # Attempt restore
    with caplog.at_level(logging.ERROR):
        result = editor.restore_tree("test.py", python_parser)
        assert not result
        assert any("Failed to restore tree from backup" in record.message 
                  for record in caplog.records)

def test_create_edit_operation_invalid_position(editor, python_parser):
    """Test creating edit operation with invalid position."""
    code = "def hello(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    
    # Try to edit at invalid position
    with pytest.raises(ParserError):
        editor.create_edit_operation(
            tree=tree,
            old_text="pass",
            new_text="return True",
            start_position=Point(1, 0)  # Invalid line number
        )

def test_multiple_sequential_edits(editor, python_parser):
    """Test applying multiple sequential edits."""
    code = "def hello(): pass"
    file_path = "test.py"
    tree = python_parser.parse(bytes(code, "utf8"))
    editor.cache_tree(file_path, tree)
    
    # Create sequence of edits
    edits = [
        # Change function name
        editor.create_edit_operation(
            tree=tree,
            old_text="hello",
            new_text="greet",
            start_position=Point(0, 4)
        ),
        # Add parameter
        editor.create_edit_operation(
            tree=tree,
            old_text="()",
            new_text="(name)",
            start_position=Point(0, 9)
        ),
        # Change body
        editor.create_edit_operation(
            tree=tree,
            old_text="pass",
            new_text='print(f"Hello {name}")',
            start_position=Point(0, 12)
        )
    ]
    
    # Apply updates
    updated_tree = editor.update_tree(file_path, edits, python_parser)
    assert updated_tree is not None
    assert updated_tree.root_node.text.decode('utf8') == 'def greet(name): print(f"Hello {name}")'

def test_update_tree_with_invalid_edits(editor, python_parser):
    """Test update_tree with edits that would create invalid code."""
    code = "def hello(): pass"
    file_path = "test.py"
    tree = python_parser.parse(bytes(code, "utf8"))
    editor.cache_tree(file_path, tree)
    
    # Create edit that would make code invalid
    invalid_edits = [
        editor.create_edit_operation(
            tree=tree,
            old_text="def hello():",
            new_text="def hello(",  # Missing closing parenthesis
            start_position=Point(0, 0)
        )
    ]
    
    # Should return None for invalid code
    assert editor.update_tree(file_path, invalid_edits, python_parser) is None

def test_source_bytes_handling(editor, python_parser):
    """Test handling of source bytes in tree operations."""
    code = "def hello(): pass"
    source_bytes = bytes(code, "utf8")
    tree = python_parser.parse(source_bytes)
    
    # Test caching with explicit source bytes
    editor.cache_tree("test.py", tree, source_bytes)
    assert editor.get_source_bytes("test.py") == source_bytes
    
    # Test getting source bytes for non-existent file
    assert editor.get_source_bytes("nonexistent.py") is None

def test_update_tree_error_handling(editor, python_parser):
    """Test error handling in update_tree method."""
    code = "def hello(): pass"
    file_path = "test.py"
    tree = python_parser.parse(bytes(code, "utf8"))
    editor.cache_tree(file_path, tree)
    
    # Test with no cached tree
    assert editor.update_tree("nonexistent.py", [], python_parser) is None
    
    # Test with invalid edit position
    invalid_edit = EditOperation(
        start_byte=1000,  # Invalid position
        old_end_byte=1004,
        new_end_byte=1004,
        start_point=Point(100, 0),
        old_end_point=Point(100, 4),
        new_end_point=Point(100, 4),
        old_text="test",
        new_text="test"
    )
    assert editor.update_tree(file_path, [invalid_edit], python_parser) is None
    
    # Test with mismatched old text
    mismatched_edit = EditOperation(
        start_byte=0,
        old_end_byte=3,
        new_end_byte=3,
        start_point=Point(0, 0),
        old_end_point=Point(0, 3),
        new_end_point=Point(0, 3),
        old_text="wrong",  # Doesn't match actual text
        new_text="test"
    )
    assert editor.update_tree(file_path, [mismatched_edit], python_parser) is None

def test_tree_sitter_parser_logging(editor, python_parser, caplog):
    """Test tree-sitter's built-in parser logging."""
    code = "def hello(): return 'world'"
    
    # Parse without logging
    tree1 = python_parser.parse(bytes(code, "utf8"))
    assert tree1 is not None
    
    # Enable logging and parse
    editor.enable_parser_logging(python_parser)
    
    # Parse with logging enabled
    tree2 = python_parser.parse(bytes(code, "utf8"))
    assert tree2 is not None
    
    # Verify log messages were captured
    # Tree-sitter v24 outputs parse and lex events
    assert any("[PARSE]" in record.message for record in caplog.records)
    assert any("[LEX]" in record.message for record in caplog.records)
    
    # Disable logging
    editor.disable_parser_logging(python_parser)
    
    # Verify logging is disabled
    caplog.clear()
    tree3 = python_parser.parse(bytes(code, "utf8"))
    assert tree3 is not None
    assert not any("[PARSE]" in record.message for record in caplog.records)
    assert not any("[LEX]" in record.message for record in caplog.records)

def test_tree_sitter_timeout(python_parser):
    """Test tree-sitter parser timeout functionality."""
    # Set a very short timeout
    python_parser.timeout_micros = 1
    
    # Try to parse complex code that should timeout
    complex_code = "def " * 1000 + ": pass"
    try:
        result = python_parser.parse(bytes(complex_code, "utf8"))
        assert result is None  # Should timeout
    except ValueError:
        # Some tree-sitter versions raise ValueError on timeout
        pass
    
    # Reset timeout and verify normal parsing works
    python_parser.timeout_micros = None
    python_parser.reset()  # Reset parser state
    
    code = "def hello(): pass"
    tree = python_parser.parse(bytes(code, "utf8"))
    assert tree is not None

def test_tree_sitter_included_ranges(python_parser):
    """Test parsing with included ranges."""
    code = """
# Python code
def hello(): pass
# More comments
def world(): return True
"""
    # Only parse the function definitions
    ranges = [
        Range(
            start_point=Point(2, 0),  # Line 2, column 0
            end_point=Point(2, 16),   # Line 2, column 16
            start_byte=14,            # Start byte of first function
            end_byte=30               # End byte of first function
        ),
        Range(
            start_point=Point(4, 0),  # Line 4, column 0
            end_point=Point(4, 23),   # Line 4, column 23
            start_byte=45,            # Start byte of second function
            end_byte=68               # End byte of second function
        )
    ]
    python_parser.included_ranges = ranges
    
    tree = python_parser.parse(bytes(code, "utf8"))
    assert tree is not None
    assert tree.included_ranges is not None
    assert len(tree.included_ranges) == 2
    
    # Reset ranges
    python_parser.included_ranges = None

def test_tree_cursor(python_parser):
    """Test tree-sitter cursor functionality."""
    code = """
def hello():
    x = 1
    y = 2
    return x + y
"""
    tree = python_parser.parse(bytes(code, "utf8"))
    cursor = tree.walk()
    
    # Navigate tree
    assert cursor.node.type == "module"
    assert cursor.goto_first_child()  # Enter function_definition
    assert cursor.node.type == "function_definition"
    
    # Test node traversal
    node_types = []
    while cursor.goto_next_sibling():
        node_types.append(cursor.node.type)
    
    # Reset cursor position
    cursor.reset(cursor.node)

def test_query_captures(python_parser, python_query):
    """Test tree-sitter query captures functionality."""
    code = """
def hello(x, y):
    return x + y

def world():
    pass
"""
    tree = python_parser.parse(bytes(code, "utf8"))
    captures = python_query.captures(tree.root_node)
    
    # Verify captures structure - should be a dict with capture names as keys
    assert isinstance(captures, dict)
    assert len(captures) > 0
    
    # Check expected capture names
    expected_captures = ['function.name', 'function.params', 'function.body']
    for capture_name in expected_captures:
        assert capture_name in captures
        assert isinstance(captures[capture_name], list)
        for node in captures[capture_name]:
            assert isinstance(node, Node)
            assert node.is_named

def test_query_matches(python_parser, python_query):
    """Test tree-sitter query matches functionality."""
    code = "def test(): return True"
    tree = python_parser.parse(bytes(code, "utf8"))
    
    matches = python_query.matches(tree.root_node)
    assert len(matches) > 0
    
    # Verify match structure
    match = matches[0]
    pattern_index, captures = match
    assert isinstance(pattern_index, int)
    assert isinstance(captures, dict)

def test_tree_edit_ranges(python_parser):
    """Test tree editing with byte ranges and points."""
    code = "def hello(): return 42"
    tree = python_parser.parse(bytes(code, "utf8"))
    
    # Edit tree directly using tree-sitter's API
    tree.edit(
        start_byte=13,          # Start of 'return'
        old_end_byte=15,        # End of 'return'
        new_end_byte=16,        # New end after edit
        start_point=(0, 13),    # Line 0, column 13
        old_end_point=(0, 15),  # Original end point
        new_end_point=(0, 16)   # New end point
    )
    
    # Verify edit was applied
    assert tree.root_node.has_changes
    
    # Reparse with new code
    new_code = "def hello(): yields 42"
    new_tree = python_parser.parse(bytes(new_code, "utf8"), tree)
    assert new_tree is not None
    
    # Check changed ranges
    changes = tree.changed_ranges(new_tree)
    assert len(changes) > 0
    for change in changes:
        assert hasattr(change, 'start_byte')
        assert hasattr(change, 'end_byte')

def test_tree_sitter_language_methods(python_language):
    """Test tree-sitter language-specific functionality."""
    # Test field name methods
    field_id = python_language.field_id_for_name('body')
    assert field_id > 0
    assert python_language.field_name_for_id(field_id) == 'body'
    
    # Test node kind methods
    function_id = python_language.id_for_node_kind('function_definition', True)
    assert function_id > 0
    assert python_language.node_kind_for_id(function_id) == 'function_definition'
    assert python_language.node_kind_is_named(function_id)
    assert python_language.node_kind_is_visible(function_id)

def test_tree_sitter_dot_graph(python_parser, tmp_path):
    """Test tree-sitter's built-in DOT graph functionality."""
    code = """
def complex_function(x, y):
    if x > y:
        return x
    return y
"""
    tree = python_parser.parse(bytes(code, "utf8"))
    
    # Use tree-sitter's print_dot_graph
    dot_file = tmp_path / "tree_sitter.dot"
    with open(dot_file, 'w') as f:
        tree.print_dot_graph(f)
    
    assert dot_file.exists()
    assert dot_file.stat().st_size > 0

def test_tree_sitter_log_handler_initialization():
    """Test TreeSitterLogHandler initialization and state."""
    handler = TreeSitterLogHandler()
    assert not handler._enabled
    assert handler.PARSE_TYPE == 0
    assert handler.LEX_TYPE == 1

def test_tree_sitter_log_handler_enable_disable():
    """Test enabling and disabling the log handler."""
    handler = TreeSitterLogHandler()
    
    # Test enable
    handler.enable()
    assert handler._enabled
    
    # Test disable
    handler.disable()
    assert not handler._enabled

def test_tree_sitter_log_handler_logging(caplog):
    """Test log message handling with different types."""
    handler = TreeSitterLogHandler()
    handler.enable()
    
    with caplog.at_level(logging.INFO):
        # Test parse message
        handler(handler.PARSE_TYPE, "Parsing function")
        assert "[PARSE] Parsing function" in caplog.text
        
        # Test lex message
        handler(handler.LEX_TYPE, "Lexing identifier")
        assert "[LEX] Lexing identifier" in caplog.text
        
        # Test disabled logging
        handler.disable()
        handler(handler.PARSE_TYPE, "Should not appear")
        assert "Should not appear" not in caplog.text

def test_tree_sitter_log_handler_parser_integration(python_parser):
    """Test log handler integration with parser."""
    handler = TreeSitterLogHandler()
    
    # Enable logging
    handler.enable_parser_logging(python_parser)
    assert python_parser.logger == handler
    
    # Disable logging
    handler.disable_parser_logging(python_parser)
    assert python_parser.logger is None

def test_cache_tree_error_handling(editor):
    """Test error handling in cache_tree method."""
    # Test with None tree
    editor.cache_tree("test.py", None)
    assert editor.get_cached_tree("test.py") is None
    
    # Test with invalid source bytes
    tree = Mock()
    tree.root_node = Mock()
    tree.root_node.text = property(lambda self: exec('raise Exception("Cannot get text")'))
    editor.cache_tree("test.py", tree)
    assert editor.get_cached_tree("test.py") is None

def test_backup_restore_error_handling(editor):
    """Test error handling in backup and restore operations."""
    # Test backup with no cached tree
    editor.backup_tree("nonexistent.py")
    assert "nonexistent.py" not in editor._tree_backups
    
    # Test restore with no backup
    assert not editor.restore_tree("nonexistent.py", Mock())
    
    # Test restore with invalid backup tree
    editor._tree_backups["test.py"] = (None, b"")
    assert not editor.restore_tree("test.py", Mock()) 