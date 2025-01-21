"""Test proper layer separation."""
import pytest
from pathlib import Path

def test_layer_separation():
    """Verify layer dependencies follow architecture."""
    import src.GithubAnalyzer.core as core
    import src.GithubAnalyzer.analysis as analysis
    import src.GithubAnalyzer.common as common

    # Core should not import from Analysis
    core_modules = [m for m in dir(core) if not m.startswith('_')]
    for module in core_modules:
        module_contents = getattr(core, module)
        if hasattr(module_contents, '__file__') and module_contents.__file__:
            assert 'analysis' not in str(module_contents.__file__)

    # Analysis can import from Core
    analysis_modules = [m for m in dir(analysis) if not m.startswith('_')]
    for module in analysis_modules:
        module_contents = getattr(analysis, module)
        if hasattr(module_contents, '__file__') and module_contents.__file__:
            assert 'GithubAnalyzer' in str(module_contents.__file__)

    # Common should not import from Core or Analysis
    common_modules = [m for m in dir(common) if not m.startswith('_')]
    for module in common_modules:
        module_contents = getattr(common, module)
        if hasattr(module_contents, '__file__') and module_contents.__file__:
            assert 'core' not in str(module_contents.__file__)
            assert 'analysis' not in str(module_contents.__file__) 