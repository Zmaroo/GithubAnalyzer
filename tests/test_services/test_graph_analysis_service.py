import pytest
from pathlib import Path
from GithubAnalyzer.core.services import GraphAnalysisService
from GithubAnalyzer.core.models.graph import (
    GraphAnalysisResult,
    CentralityMetrics,
    CommunityDetection,
    PathAnalysis
)

@pytest.fixture
def graph_service():
    """Create a graph analysis service instance"""
    return GraphAnalysisService()

@pytest.fixture
def sample_codebase(tmp_path):
    """Create a sample codebase structure"""
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    
    # Create a module with dependencies
    module_dir = repo_dir / "module"
    module_dir.mkdir()
    
    # Main module file
    (module_dir / "main.py").write_text("""
from .utils import helper
from .models import User

class UserService:
    def __init__(self):
        self.helper = helper.Helper()
    
    def get_user(self, user_id: int) -> User:
        return self.helper.fetch_user(user_id)
""")
    
    # Utils module
    utils_dir = module_dir / "utils"
    utils_dir.mkdir()
    (utils_dir / "helper.py").write_text("""
from ..models import User
from ..database import db

class Helper:
    def fetch_user(self, user_id: int) -> User:
        return db.query(User).get(user_id)
""")
    
    # Models module
    (module_dir / "models.py").write_text("""
class User:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
""")
    
    # Database module
    (module_dir / "database.py").write_text("""
class Database:
    def query(self, model):
        pass

db = Database()
""")
    
    return repo_dir

def test_graph_analysis_initialization(graph_service):
    """Test graph service initialization"""
    assert graph_service is not None
    assert graph_service.graph_name == "code_analysis_graph"

def test_analyze_code_structure(graph_service, sample_codebase):
    """Test full code structure analysis"""
    result = graph_service.analyze_code_structure(str(sample_codebase))
    
    assert isinstance(result, GraphAnalysisResult)
    assert result.centrality is not None
    assert result.communities is not None
    assert result.paths is not None
    
    # Check centrality metrics
    assert len(result.centrality.pagerank) > 0
    assert len(result.centrality.betweenness) > 0
    
    # Check dependency detection
    assert result.dependencies is not None
    assert any(
        'UserService' in str(deps)
        for deps in result.dependencies.dependency_hubs
    )

def test_ast_pattern_analysis(graph_service, sample_codebase):
    """Test AST pattern analysis"""
    patterns = graph_service.analyze_ast_patterns()
    
    assert patterns is not None
    assert 'ast_patterns' in patterns
    assert 'complexity_analysis' in patterns
    
    # Check pattern detection
    ast_patterns = patterns['ast_patterns']
    assert any(p['pattern_type'] == 'ClassDef' for p in ast_patterns)
    assert any(p['pattern_type'] == 'FunctionDef' for p in ast_patterns)

def test_dependency_analysis(graph_service, sample_codebase):
    """Test dependency structure analysis"""
    deps = graph_service.analyze_dependency_structure()
    
    assert deps is not None
    assert 'circular_dependencies' in deps
    assert 'dependency_hubs' in deps
    assert 'dependency_clusters' in deps
    
    # Check circular dependency detection
    circular = deps['circular_dependencies']
    assert isinstance(circular, list)
    
    # Check dependency hubs
    hubs = deps['dependency_hubs']
    assert any('models.User' in str(hub) for hub in hubs)

def test_code_evolution_analysis(graph_service, sample_codebase):
    """Test code evolution analysis"""
    evolution = graph_service.analyze_code_evolution()
    
    assert evolution is not None
    assert 'change_hotspots' in evolution
    assert 'cochange_patterns' in evolution

def test_refactoring_suggestions(graph_service, sample_codebase):
    """Test refactoring suggestion generation"""
    suggestions = graph_service.get_refactoring_suggestions()
    
    assert suggestions is not None
    assert 'coupling_based' in suggestions
    assert 'abstraction_based' in suggestions
    
    # Check suggestion quality
    coupling_suggestions = suggestions['coupling_based']
    assert all(s['coupling_score'] > 0.5 for s in coupling_suggestions)

def test_ast_metrics_correlation(graph_service, sample_codebase):
    """Test AST metrics correlation"""
    metrics = graph_service.correlate_ast_metrics()
    
    assert metrics is not None
    assert all(
        'function_name' in m and
        'ast_complexity' in m and
        'dependency_score' in m
        for m in metrics
    )

def test_error_handling(graph_service):
    """Test error handling for invalid inputs"""
    # Test with nonexistent path
    result = graph_service.analyze_code_structure("/nonexistent/path")
    assert result is None
    
    # Test with invalid graph name
    graph_service.graph_name = "invalid_graph"
    patterns = graph_service.analyze_ast_patterns()
    assert patterns == {}

@pytest.mark.parametrize("method_name", [
    "analyze_code_structure",
    "analyze_ast_patterns",
    "analyze_dependency_structure",
    "analyze_code_evolution",
    "get_refactoring_suggestions",
    "correlate_ast_metrics"
])
def test_method_robustness(graph_service, method_name):
    """Test robustness of all analysis methods"""
    method = getattr(graph_service, method_name)
    result = method()
    
    # Should handle errors gracefully
    assert result is None or isinstance(result, (dict, GraphAnalysisResult)) 