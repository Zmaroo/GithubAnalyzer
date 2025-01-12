import pytest
from pathlib import Path
from GithubAnalyzer.core.services import AnalyzerService
from GithubAnalyzer.core.models import (
    ModuleInfo,
    FunctionInfo,
    ClassInfo,
    AnalysisResult
)

@pytest.fixture
def analyzer_service():
    """Create an analyzer service instance"""
    return AnalyzerService()

@pytest.fixture
def sample_repo(tmp_path):
    """Create a sample repository structure"""
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    
    # Create Python module
    module_dir = repo_dir / "module"
    module_dir.mkdir()
    (module_dir / "__init__.py").write_text("")
    
    # Create main code file
    (module_dir / "main.py").write_text("""
\"\"\"Main module docstring\"\"\"
from typing import List, Optional

class BaseClass:
    \"\"\"Base class docstring\"\"\"
    def __init__(self):
        self.value = 0

class MainClass(BaseClass):
    \"\"\"Main class docstring\"\"\"
    def process(self, data: List[str]) -> Optional[str]:
        \"\"\"Process the data\"\"\"
        if not data:
            return None
        return data[0].upper()

def helper_function(x: int) -> bool:
    \"\"\"Helper function docstring\"\"\"
    return x > 0
""")

    # Create test file
    (module_dir / "test_main.py").write_text("""
import pytest
from .main import MainClass

def test_process():
    obj = MainClass()
    assert obj.process(["test"]) == "TEST"
""")

    # Add documentation
    (repo_dir / "README.md").write_text("""
# Sample Project
A test project.
""")
    
    return repo_dir

def test_analyzer_initialization(analyzer_service):
    """Test analyzer service initialization"""
    assert analyzer_service is not None
    assert analyzer_service.current_file is None

def test_analyze_repository(analyzer_service, sample_repo):
    """Test full repository analysis"""
    result = analyzer_service.analyze_repository(str(sample_repo))
    
    assert isinstance(result, AnalysisResult)
    assert result.modules
    assert not result.errors
    
    # Check module detection
    module_paths = {m.path for m in result.modules}
    assert any('main.py' in p for p in module_paths)
    assert any('test_main.py' in p for p in module_paths)
    
    # Find main module
    main_module = next(m for m in result.modules if 'main.py' in m.path)
    
    # Check class detection
    assert len(main_module.classes) == 2
    assert any(c.name == 'BaseClass' for c in main_module.classes)
    assert any(c.name == 'MainClass' for c in main_module.classes)
    
    # Check inheritance
    main_class = next(c for c in main_module.classes if c.name == 'MainClass')
    assert 'BaseClass' in main_class.bases
    
    # Check function detection
    assert any(f.name == 'helper_function' for f in main_module.functions)
    
    # Check method detection
    assert any(
        m.name == 'process' 
        for c in main_module.classes 
        for m in c.methods
    )

def test_analyze_single_file(analyzer_service, sample_repo):
    """Test single file analysis"""
    file_path = str(sample_repo / "module" / "main.py")
    module_info = analyzer_service.analyze_file(file_path)
    
    assert isinstance(module_info, ModuleInfo)
    assert module_info.path == file_path
    assert len(module_info.classes) == 2
    assert len(module_info.functions) == 1
    
    # Check function details
    helper = module_info.functions[0]
    assert helper.name == 'helper_function'
    assert helper.docstring
    assert helper.args == ['x']
    assert helper.returns == 'bool'

def test_analyze_empty_repository(analyzer_service, tmp_path):
    """Test analyzing empty repository"""
    result = analyzer_service.analyze_repository(str(tmp_path))
    
    assert isinstance(result, AnalysisResult)
    assert not result.modules
    assert not result.errors

def test_analyze_nonexistent_path(analyzer_service):
    """Test handling nonexistent paths"""
    result = analyzer_service.analyze_repository("/nonexistent/path")
    
    assert isinstance(result, AnalysisResult)
    assert not result.modules
    assert result.errors

def test_analyze_invalid_python(analyzer_service, tmp_path):
    """Test handling invalid Python code"""
    invalid_file = tmp_path / "invalid.py"
    invalid_file.write_text("""
def broken_function(
    print("Missing parenthesis"
""")
    
    module_info = analyzer_service.analyze_file(str(invalid_file))
    assert module_info is None or not module_info.functions
 