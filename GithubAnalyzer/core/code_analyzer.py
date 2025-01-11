import ast
import os
import traceback
from typing import Dict, Any, List, Optional, Union
from .models import (
    FunctionInfo, 
    DocumentationInfo,
    DocstringVisitor,
    DocstringInfo,
    RepositoryAnalysis,
    CodeRelationships,
    ComplexityVisitor,
    FileAnalysisResult,
    ClassInfo,
    ModuleInfo,
    AnalysisContext,
    AnalysisError,
    CodeQualityMetrics,
    SecurityAnalysisResult,
    PerformanceMetrics,
    AnalysisConfig,
    AnalysisProgress
)
from .database_utils import DatabaseManager
from .documentation_analyzer import DocumentationAnalyzer
from .code_parser import CodeParser
import networkx as nx
import math
from .registry import BusinessTools
from .patterns import PatternDetector
from .utils import setup_logger

logger = setup_logger(__name__)

class CodeAnalyzer:
    """Analyzes code structure and relationships"""
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.current_file = None
        self.doc_analyzer = DocumentationAnalyzer()
        self.code_parser = CodeParser()
        self.tools = BusinessTools.create()
        
    def analyze_repository(self, repo_path: str) -> RepositoryAnalysis:
        """Analyze entire repository"""
        try:
            analysis = RepositoryAnalysis(
                codebase_understanding={},
                discovered_modules=[],
                external_dependencies=[],
                dependency_graph=nx.DiGraph(),
                documentation=[],
                functions=[],
                relationships=CodeRelationships()
            )
            
            # Analyze project structure
            for root, _, files in os.walk(repo_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Analyze dependencies
                    if file in ['pyproject.toml', 'setup.py', 'requirements.txt']:
                        deps = self.analyze_dependencies(file_path)
                        if deps:
                            analysis.external_dependencies.extend(deps)
                            
                    # Analyze Python files
                    elif file.endswith('.py'):
                        module_info = self.analyze_python_file(file_path)
                        if module_info:
                            analysis.discovered_modules.append(module_info)
                            
                            # Add to dependency graph
                            for imp in module_info.get('imports', []):
                                import_name = imp.get('name') if isinstance(imp, dict) else str(imp)
                                analysis.dependency_graph.add_edge(module_info['path'], import_name)
                                
                    # Analyze documentation
                    elif file.endswith(('.md', '.rst', '.txt')):
                        doc_info = self.analyze_documentation_file(file_path)
                        if doc_info:
                            analysis.documentation.append(doc_info)
            
            # Build relationships
            analysis.relationships = self._build_code_relationships(analysis.discovered_modules)
            
            # Store in database
            self.db_manager.store_code_relationships(analysis.relationships)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            logger.error(traceback.format_exc())
            return None

    def _build_code_relationships(self, modules: List[Dict[str, Any]]) -> CodeRelationships:
        """Build code relationships from analyzed modules"""
        relationships = CodeRelationships()
        
        for module in modules:
            # Add functions with their relationships
            for func in module.get('functions', []):
                relationships.functions.append({
                    'name': func['name'],
                    'file_path': module['path'],
                    'calls': func.get('calls', []),
                    'imports': func.get('imports', [])
                })
                
            # Add classes with their relationships
            for cls in module.get('classes', []):
                relationships.classes.append({
                    'name': cls['name'],
                    'file_path': module['path'],
                    'bases': cls.get('bases', []),
                    'methods': cls.get('methods', [])
                })
                
            # Add imports
            for imp in module.get('imports', []):
                relationships.imports.append({
                    'name': imp['name'] if isinstance(imp, dict) else str(imp),
                    'file_path': module['path']
                })
                
        return relationships

    def analyze_file(self, file_path: str) -> Union[List[FunctionInfo], List[DocumentationInfo]]:
        """Analyze a file using appropriate parser"""
        self.current_file = file_path
        
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist")
            return []
        if not os.access(file_path, os.R_OK):
            logger.error(f"File {file_path} is not readable")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().replace('\r\n', '\n').replace('\r', '\n')
            
            if not content.strip():
                logger.warning(f"File {file_path} is empty")
                return []
            
            ext = os.path.splitext(file_path)[1].lower()
            
            # Use appropriate parser based on file type
            if ext == '.py':
                return self.analyze_python_file(file_path)
            elif ext in ['.md', '.rst', '.txt']:
                return self.analyze_documentation_file(file_path)
            else:
                logger.warning(f"Unsupported file type: {ext}")
                return []
                
        except UnicodeDecodeError:
            logger.warning(f"File {file_path} contains invalid UTF-8, trying with errors='replace'")
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return self.analyze_content(content, file_path)
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def analyze_python_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single Python file"""
        try:
            # Use new code parser
            parse_result = self.code_parser.parse_file(file_path)
            if "error" in parse_result:
                logger.error(f"Error parsing {file_path}: {parse_result['error']}")
                return None

            module_info = {
                'path': file_path,
                'imports': [],
                'functions': [],
                'classes': [],
                'docstrings': []
            }

            # Extract imports from semantic information
            for imp in parse_result["semantic"]["imports"]:
                module_info['imports'].append({
                    'name': imp["text"],
                    'asname': None  # Could be enhanced with more parsing
                })

            # Extract functions
            for func in parse_result["semantic"]["functions"]:
                module_info['functions'].append({
                    'name': func["text"],
                    'lineno': func["range"]["start"][0] + 1,
                    'args': []  # Could be enhanced with parameter parsing
                })

            # Extract classes
            for cls in parse_result["semantic"]["classes"]:
                module_info['classes'].append({
                    'name': cls["text"],
                    'lineno': cls["range"]["start"][0] + 1,
                    'bases': []  # Could be enhanced with inheritance parsing
                })

            # Get docstrings using existing visitor
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            docstring_visitor = DocstringVisitor()
            docstring_visitor.visit(tree)
            module_info['docstrings'] = [d.__dict__ for d in docstring_visitor.docstrings]

            return module_info

        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def analyze_dependencies(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze project dependencies from requirements or setup files"""
        try:
            dependencies = []
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.endswith('requirements.txt'):
                # Parse requirements.txt
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('==')
                        if len(parts) == 2:
                            dependencies.append({
                                'name': parts[0],
                                'version': parts[1],
                                'type': 'requirement'
                            })
                        else:
                            dependencies.append({
                                'name': line,
                                'version': None,
                                'type': 'requirement'
                            })
                            
            elif file_path.endswith('setup.py'):
                # Parse setup.py
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and hasattr(node.func, 'id'):
                        if node.func.id == 'setup':
                            for kw in node.keywords:
                                if kw.arg in ['install_requires', 'requires']:
                                    if isinstance(kw.value, ast.List):
                                        for elt in kw.value.elts:
                                            if isinstance(elt, ast.Str):
                                                dependencies.append({
                                                    'name': elt.s,
                                                    'type': 'setup'
                                                })
                                                
            elif file_path.endswith('pyproject.toml'):
                try:
                    import tomli
                    data = tomli.loads(content)
                    if 'project' in data and 'dependencies' in data['project']:
                        for dep in data['project']['dependencies']:
                            dependencies.append({
                                'name': dep,
                                'type': 'pyproject'
                            })
                except ImportError:
                    logger.warning("tomli not installed, skipping pyproject.toml parsing")
                    
            return dependencies
            
        except Exception as e:
            logger.error(f"Error analyzing dependencies in {file_path}: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def analyze_documentation_file(self, file_path: str) -> Optional[DocumentationInfo]:
        """Analyze documentation files using DocumentationAnalyzer"""
        return self.doc_analyzer.analyze_file(file_path)

    def analyze_patterns(self, code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze code patterns"""
        try:
            parse_result = self.code_parser.parse_file(file_path) if file_path else self.code_parser.parse_content(code)
            return PatternDetector.detect_all(parse_result, file_path)
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return {}

    def analyze_code_quality(self, code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze code quality metrics
        
        Returns:
            Dict containing:
            - complexity metrics
            - maintainability metrics
            - test coverage
            - documentation quality
        """
        try:
            # Try cache first
            if file_path:
                cached = self.db_manager.get_from_cache(file_path, "quality")
                if cached:
                    return cached

            quality_metrics = {
                'complexity': PatternDetector.detect_complexity_patterns(code),
                'maintainability': self._assess_maintainability(code),
                'test_coverage': self._analyze_test_coverage(code),
                'documentation_quality': self._assess_documentation(code)
            }

            # Cache results
            if file_path:
                self.db_manager.store_in_cache(file_path, "quality", quality_metrics)

            return quality_metrics

        except Exception as e:
            logger.error(f"Error analyzing code quality: {e}")
            return {}

    def _assess_maintainability(self, code: str) -> Dict[str, float]:
        """Assess code maintainability"""
        try:
            lines = code.split('\n')
            loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            comments = len([l for l in lines if l.strip().startswith('#')])
            
            # Calculate Maintainability Index
            # MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
            halstead_volume = self._calculate_complexity(code)['halstead']
            cyclomatic = self._calculate_complexity(code)['cyclomatic']
            
            mi_score = 171 - 5.2 * math.log(halstead_volume or 1) - \
                      0.23 * cyclomatic - 16.2 * math.log(loc or 1)
            
            return {
                'mi_score': max(0, min(100, mi_score)),
                'loc': loc,
                'comment_ratio': comments / loc if loc > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error assessing maintainability: {e}")
            return {'mi_score': 0.0, 'loc': 0, 'comment_ratio': 0.0}
