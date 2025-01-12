import pytest
from pathlib import Path
from GithubAnalyzer.core.registry import BusinessTools
from GithubAnalyzer.core.models import (
    ModuleInfo,
    AnalysisResult,
    RepositoryInfo,
    RepositoryState
)

@pytest.fixture
def business_tools():
    """Create properly initialized business tools"""
    tools = BusinessTools.create()
    yield tools
    tools.database_service.cleanup()

@pytest.fixture
def complex_project(tmp_path):
    """Create a complex project with multiple frameworks and file types"""
    project_dir = tmp_path / "complex_project"
    project_dir.mkdir()
    
    # FastAPI with SQLAlchemy and Pydantic
    api_dir = project_dir / "api"
    api_dir.mkdir()
    (api_dir / "main.py").write_text("""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

app = FastAPI()

class UserModel(BaseModel):
    id: int
    name: str

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return {"id": user_id, "name": "test"}
""")

    # Django app
    django_dir = project_dir / "admin"
    django_dir.mkdir()
    (django_dir / "views.py").write_text("""
from django.views import View
from django.http import JsonResponse

class AdminView(View):
    def get(self, request):
        return JsonResponse({"admin": True})
""")

    # Configuration files
    (project_dir / "pyproject.toml").write_text("""
[tool.poetry]
name = "complex-project"
version = "0.1.0"
""")
    
    (project_dir / "config.yaml").write_text("""
database:
  url: postgresql://localhost/db
""")

    # Documentation
    (project_dir / "README.md").write_text("""
# Complex Project
Multiple frameworks example.
""")
    
    return project_dir

def test_complex_analysis_flow(business_tools, complex_project):
    """Test analysis of complex project with multiple frameworks"""
    # Start analysis and track state
    state = RepositoryState(
        url="test_url",
        status="analyzing",
        progress=0.0,
        current_operation="Starting analysis"
    )
    business_tools.database_service.store_repository_state(state)
    
    # Analyze repository
    result = business_tools.analyzer_service.analyze_repository(
        str(complex_project)
    )
    assert isinstance(result, AnalysisResult)
    assert result.modules
    
    # Check framework detection across files
    frameworks_found = set()
    for module in result.modules:
        if module.path.endswith('.py'):
            frameworks = business_tools.framework_service.detect_frameworks(module)
            frameworks_found.update(frameworks.keys())
    
    # Should detect multiple frameworks
    assert 'fastapi' in frameworks_found
    assert 'django' in frameworks_found
    assert 'sqlalchemy' in frameworks_found
    assert 'pydantic' in frameworks_found
    
    # Check config file parsing
    config_files = [m for m in result.modules if m.path.endswith(('.yaml', '.toml'))]
    assert len(config_files) == 2
    
    # Update and verify repository state
    state.status = "completed"
    state.progress = 1.0
    business_tools.database_service.store_repository_state(state)
    
    stored_state = business_tools.database_service.get_repository_state("test_url")
    assert stored_state.status == "completed"

def test_concurrent_analysis(business_tools, complex_project):
    """Test handling concurrent analysis of same repository"""
    # Start first analysis
    state1 = RepositoryState(
        url="test_url",
        status="analyzing",
        progress=0.0
    )
    business_tools.database_service.store_repository_state(state1)
    
    # Try to start second analysis
    state2 = RepositoryState(
        url="test_url",
        status="analyzing",
        progress=0.0
    )
    # Should not override first analysis
    stored = business_tools.database_service.get_repository_state("test_url")
    assert stored.progress == state1.progress

def test_incremental_analysis(business_tools, complex_project):
    """Test incremental analysis with cached results"""
    # First analysis
    result1 = business_tools.analyzer_service.analyze_repository(
        str(complex_project)
    )
    
    # Cache results
    business_tools.database_service.cache_analysis_result(
        "test_url:analysis",
        result1
    )
    
    # Modify a file
    api_file = complex_project / "api" / "main.py"
    original_content = api_file.read_text()
    api_file.write_text(original_content + "\n# Modified")
    
    # Second analysis should use cache for unchanged files
    result2 = business_tools.analyzer_service.analyze_repository(
        str(complex_project)
    )
    
    # Compare results
    assert len(result1.modules) == len(result2.modules)
    modified_module = next(
        m for m in result2.modules 
        if m.path.endswith("main.py")
    )
    assert "Modified" in modified_module.documentation[-1].content

def test_error_recovery(business_tools, complex_project):
    """Test recovery from errors during analysis"""
    # Create invalid file
    (complex_project / "invalid.py").write_text("def broken(")
    
    # Analysis should continue despite error
    result = business_tools.analyzer_service.analyze_repository(
        str(complex_project)
    )
    
    assert result.success
    assert len(result.errors) == 1  # Only invalid.py should fail
    assert len(result.modules) > 0  # Other files should be analyzed 