"""Complex integration tests"""
import pytest
from pathlib import Path
from GithubAnalyzer.core.registry import AnalysisToolRegistry

@pytest.fixture
def common_ops(registry):
    """Get common operations interface"""
    return registry.get_common_operations()

# Update other test files similarly 