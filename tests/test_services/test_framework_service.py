import pytest
from GithubAnalyzer.core.services import FrameworkService
from GithubAnalyzer.core.models import ModuleInfo

@pytest.fixture
def framework_service():
    """Create a framework service instance"""
    return FrameworkService()

@pytest.fixture
def django_module():
    """Create a Django module info"""
    return ModuleInfo(
        path="views.py",
        imports=["django.views", "django.http"],
        functions=[],
        classes=[{
            "name": "HomeView",
            "docstring": "Home page view",
            "methods": [
                {
                    "name": "get",
                    "docstring": "Handle GET request",
                    "args": ["self", "request"]
                }
            ]
        }]
    )

def test_framework_detection(framework_service, django_module):
    """Test framework detection"""
    results = framework_service.detect_frameworks(django_module)
    
    assert 'django' in results
    assert results['django'] > 0.5  # High confidence

def test_multiple_frameworks(framework_service):
    """Test detecting multiple frameworks"""
    module = ModuleInfo(
        path="api.py",
        imports=["fastapi", "sqlalchemy", "pydantic"],
        functions=[],
        classes=[]
    )
    
    results = framework_service.detect_frameworks(module)
    assert 'fastapi' in results
    assert 'sqlalchemy' in results
    assert 'pydantic' in results

def test_no_framework(framework_service):
    """Test when no framework is used"""
    module = ModuleInfo(
        path="utils.py",
        imports=["typing", "datetime"],
        functions=[],
        classes=[]
    )
    
    results = framework_service.detect_frameworks(module)
    assert not results 