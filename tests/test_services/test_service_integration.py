import pytest
from pathlib import Path
from GithubAnalyzer.core.services import (
    ParserService,
    AnalyzerService,
    DatabaseService,
    FrameworkService
)
from GithubAnalyzer.core.registry import BusinessTools
from GithubAnalyzer.core.models import (
    ModuleInfo,
    AnalysisResult,
    RepositoryInfo
)

@pytest.fixture
def business_tools():
    """Create properly initialized business tools"""
    tools = BusinessTools.create()
    yield tools
    # Cleanup
    tools.database_service.cleanup()

@pytest.fixture
def sample_django_project(tmp_path):
    """Create a sample Django project structure"""
    project_dir = tmp_path / "django_project"
    project_dir.mkdir()
    
    # Create Django files
    (project_dir / "manage.py").write_text("""
#!/usr/bin/env python
import os
import sys
from django.core.management import execute_from_command_line
execute_from_command_line(sys.argv)
""")

    # Create views
    views_dir = project_dir / "myapp" / "views"
    views_dir.mkdir(parents=True)
    (views_dir / "__init__.py").write_text("")
    (views_dir / "main.py").write_text("""
from django.views import View
from django.http import JsonResponse

class HomeView(View):
    \"\"\"Home page view\"\"\"
    def get(self, request):
        return JsonResponse({"status": "ok"})
""")
    
    return project_dir

def test_full_analysis_flow(business_tools, sample_django_project):
    """Test complete analysis flow through all services"""
    # 1. Analyze repository
    result = business_tools.analyzer_service.analyze_repository(
        str(sample_django_project)
    )
    assert isinstance(result, AnalysisResult)
    assert result.modules
    assert not result.errors
    
    # 2. Detect frameworks
    django_files = [m for m in result.modules if 'views' in m.path]
    assert django_files
    
    framework_results = business_tools.framework_service.detect_frameworks(
        django_files[0]
    )
    assert 'django' in framework_results
    assert framework_results['django'] > 0.5
    
    # 3. Store results
    repo_info = RepositoryInfo(
        name="django_test",
        url="test_url",
        local_path=str(sample_django_project),
        metadata={
            "frameworks": framework_results,
            "analysis": result
        }
    )
    
    success = business_tools.database_service.store_repository_info(repo_info)
    assert success
    
    # 4. Verify storage and cache
    stored = business_tools.database_service.get_repository_info("test_url")
    assert stored is not None
    assert stored.metadata["frameworks"]["django"] > 0.5

def test_parser_analyzer_integration(business_tools, tmp_path):
    """Test integration between parser and analyzer"""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("""
class TestClass:
    def method(self):
        pass
""")
    
    # Parse file
    with open(test_file) as f:
        parse_result = business_tools.parser_service.parse_file(
            str(test_file),
            f.read()
        )
    
    assert parse_result.success
    assert parse_result.semantic
    
    # Analyze parsed result
    module_info = business_tools.analyzer_service.analyze_file(str(test_file))
    assert isinstance(module_info, ModuleInfo)
    assert len(module_info.classes) == 1
    assert module_info.classes[0].name == "TestClass"

def test_framework_database_integration(business_tools, sample_django_project):
    """Test framework detection and storage integration"""
    # Analyze and detect frameworks
    module_info = ModuleInfo(
        path=str(sample_django_project / "myapp" / "views" / "main.py"),
        imports=["django.views", "django.http"],
        functions=[],
        classes=[{
            "name": "HomeView",
            "methods": [{"name": "get"}]
        }]
    )
    
    frameworks = business_tools.framework_service.detect_frameworks(module_info)
    assert frameworks
    
    # Store framework information
    repo_info = RepositoryInfo(
        name="test_repo",
        url="test_url",
        local_path=str(sample_django_project),
        metadata={"frameworks": frameworks}
    )
    
    success = business_tools.database_service.store_repository_info(repo_info)
    assert success
    
    # Verify storage
    stored = business_tools.database_service.get_repository_info("test_url")
    assert stored.metadata["frameworks"] == frameworks

def test_error_propagation(business_tools, tmp_path):
    """Test error handling and propagation between services"""
    # Create invalid Python file
    invalid_file = tmp_path / "invalid.py"
    invalid_file.write_text("def broken(")
    
    # Parsing should fail
    with open(invalid_file) as f:
        parse_result = business_tools.parser_service.parse_file(
            str(invalid_file),
            f.read()
        )
    assert not parse_result.success
    assert parse_result.errors
    
    # Analysis should handle parse failure
    module_info = business_tools.analyzer_service.analyze_file(str(invalid_file))
    assert module_info is None or not module_info.functions 