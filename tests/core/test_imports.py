"""Test core module imports."""
import pytest
import importlib
import ast
from pathlib import Path

def has_tree_sitter_usage(content: str) -> bool:
    """Check if code actually uses tree-sitter."""
    tree = ast.parse(content)
    
    class TreeSitterVisitor(ast.NodeVisitor):
        def __init__(self):
            self.uses_tree_sitter = False
            
        def visit_Import(self, node):
            for name in node.names:
                if 'tree_sitter' in name.name:
                    self.uses_tree_sitter = True
            self.generic_visit(node)
            
        def visit_ImportFrom(self, node):
            if 'tree_sitter' in node.module:
                self.uses_tree_sitter = True
            self.generic_visit(node)
            
    visitor = TreeSitterVisitor()
    visitor.visit(tree)
    return visitor.uses_tree_sitter

def test_core_imports():
    """Test all core module imports."""
    # Core models
    from src.GithubAnalyzer.core.models import ast, errors, file
    # Core services
    from src.GithubAnalyzer.core.services import (
        base_service,
        file_service,
        parser_service
    )
    from src.GithubAnalyzer.core.services.parsers import base, config_parser
    # Core config
    from src.GithubAnalyzer.core.config import settings, parser_config, language_config
    # Core utils
    from src.GithubAnalyzer.core.utils import context_manager, decorators, logging

    # Check each core module for analysis and tree-sitter usage
    core_modules = [
        'src.GithubAnalyzer.core.models.ast',
        'src.GithubAnalyzer.core.models.errors',
        'src.GithubAnalyzer.core.models.file',
        'src.GithubAnalyzer.core.services.base_service',
        'src.GithubAnalyzer.core.services.file_service',
        'src.GithubAnalyzer.core.services.parser_service',
        'src.GithubAnalyzer.core.services.parsers.base',
        'src.GithubAnalyzer.core.services.parsers.config_parser',
    ]

    for module_name in core_modules:
        module = importlib.import_module(module_name)
        module_file = module.__file__
        with open(module_file, 'r') as f:
            content = f.read()
            # Check for analysis imports
            assert 'from src.GithubAnalyzer.analysis' not in content, \
                f"{module_name} should not import from analysis layer"
            assert 'import src.GithubAnalyzer.analysis' not in content, \
                f"{module_name} should not import from analysis layer"
            # Check for actual tree-sitter usage
            assert not has_tree_sitter_usage(content), \
                f"{module_name} should not use tree-sitter"

    # Verify core modules don't use tree-sitter
    core_path = Path(module.__file__).parent.parent
    for py_file in core_path.rglob('*.py'):
        with open(py_file, 'r') as f:
            content = f.read()
            assert not has_tree_sitter_usage(content), \
                f"{py_file} should not use tree-sitter" 