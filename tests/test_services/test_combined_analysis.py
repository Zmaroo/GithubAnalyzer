import pytest
from GithubAnalyzer.core.services import GraphAnalysisService
from GithubAnalyzer.core.models.graph import (
    ASTPattern,
    CombinedAnalysis
)

@pytest.fixture
def complex_codebase(tmp_path):
    """Create a complex codebase for testing combined analysis"""
    repo_dir = tmp_path / "complex_repo"
    repo_dir.mkdir()
    
    # Create a file with complex patterns
    (repo_dir / "complex.py").write_text("""
class ComplexClass:
    def method1(self, x):
        if x > 0:
            for i in range(x):
                if i % 2 == 0:
                    yield i
                else:
                    continue
    
    def method2(self, data):
        try:
            result = []
            for item in data:
                if isinstance(item, dict):
                    if 'key' in item:
                        result.append(item['key'])
                    else:
                        result.append(None)
            return result
        except Exception as e:
            return []
""")
    
    return repo_dir

@pytest.fixture
def graph_service():
    """Create a graph analysis service instance"""
    service = GraphAnalysisService()
    service.initialize()
    return service

def test_combined_analysis(graph_service, complex_codebase):
    """Test combined AST and graph analysis"""
    # Analyze code structure
    result = graph_service.analyze_code_structure(str(complex_codebase))
    assert result is not None
    assert result.ast_analysis is not None
    
    # Check AST patterns
    ast_patterns = result.ast_analysis.ast_patterns
    assert any(
        p.pattern_type == 'if_nesting' 
        for p in ast_patterns
    )
    
    # Check complexity correlation
    assert result.ast_analysis.correlated_metrics is not None
    assert any(
        'method2' in str(hotspot)
        for hotspot in result.ast_analysis.complexity_hotspots
    )

def test_complexity_threshold(graph_service, complex_codebase):
    """Test complexity threshold calculation"""
    result = graph_service.analyze_code_structure(str(complex_codebase))
    assert result is not None
    
    threshold = result.get_complexity_threshold()
    assert threshold > 0
    
    hotspots = result.get_complexity_hotspots()
    assert len(hotspots) > 0
    assert 'method2' in str(hotspots) 