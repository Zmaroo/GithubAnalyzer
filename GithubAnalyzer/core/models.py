from typing import List, Optional, Dict, Any, Literal, Union
from dataclasses import dataclass, field
import numpy as np
from neo4j import GraphDatabase, Session
import logging
from sentence_transformers import SentenceTransformer
import ast
import networkx as nx
from GithubAnalyzer.core.database_utils import DatabaseManager
import math
import time

logger = logging.getLogger(__name__)

@dataclass
class DocumentationInfo:
    """Information about a documentation file"""
    file_path: str
    content: str
    doc_type: Literal['markdown', 'rst', 'txt'] = 'markdown'
    title: str = ""
    section_headers: List[str] = field(default_factory=list)

@dataclass
class TreeSitterNode:
    """Tree-sitter AST node representation"""
    type: str
    text: str
    start_point: tuple
    end_point: tuple
    children: List['TreeSitterNode']

@dataclass
class FunctionInfo:
    """Information about a function/method"""
    name: str
    file_path: str
    docstring: str = ""
    params: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    calls: Set[str] = field(default_factory=set)
    complexity: int = 0
    lines: int = 0
    nested_depth: int = 0
    start_line: int = 0
    end_line: int = 0
    imports: List[str] = field(default_factory=list)

@dataclass
class CodeAnalysisResult:
    """Results from code analysis"""
    modules: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]
    structure: Dict[str, Any]
    functions: List[FunctionInfo] = field(default_factory=list)
    documentation: List[DocumentationInfo] = field(default_factory=list)

@dataclass
class QueryContext:
    """Context for code queries"""
    repository: str
    file_path: Optional[str] = None
    code_snippet: Optional[str] = None
    analysis_result: Optional[ContextAnalysisResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RepositoryInfo:
    """Information about a repository"""
    name: str
    url: str
    local_path: str
    last_analyzed: Optional[str] = None
    is_current: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CodeRelationships:
    """Code relationship information"""
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    imports: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class GraphDBOperations:
    """Graph database operations"""
    session: Session
    relationships: CodeRelationships

    def store_relationships(self) -> bool:
        """Store relationships in graph database"""
        try:
            # Implementation moved to DatabaseManager
            return True
        except Exception as e:
            logger.error(f"Error storing relationships: {e}")
            return False

@dataclass
class ContextAnalysisResult:
    """Results from context analysis"""
    imports: List[str] = field(default_factory=list)
    related_functions: List[str] = field(default_factory=list)
    class_hierarchy: List[Dict[str, Any]] = field(default_factory=list)
    project_patterns: List[str] = field(default_factory=list)
    framework_patterns: List[str] = field(default_factory=list)
    style_patterns: List[str] = field(default_factory=list)
    usage_patterns: List[str] = field(default_factory=list)
    embeddings: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QueryProcessorResult:
    """Results from query processing"""
    response: str
    confidence: float = 0.0
    relevant_code: Optional[str] = None
    documentation_matches: List[str] = field(default_factory=list)
    context_used: Dict[str, Any] = field(default_factory=dict)

class CodeContextAnalyzer:
    """Analyzes code context"""
    target_line: Optional[int] = None
    
    def analyze_context(self, code: str, target_line: Optional[int] = None) -> ContextAnalysisResult:
        """Analyze code context"""
        result = ContextAnalysisResult()
        try:
            tree = ast.parse(code)
            visitor = self._create_ast_visitor(target_line)
            visitor.visit(tree)
            
            # Fill in basic context
            result.imports = visitor.imports
            result.related_functions = visitor.functions
            result.class_hierarchy = visitor.class_hierarchy
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
            return result

    def _create_ast_visitor(self, target_line: Optional[int] = None) -> 'ContextVisitor':
        """Create AST visitor for context analysis"""
        return ContextVisitor(target_line)

@dataclass
class ContextVisitor(ast.NodeVisitor):
    """AST visitor for context analysis"""
    target_line: Optional[int] = None
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    class_hierarchy: List[Dict[str, Any]] = field(default_factory=list)
    current_class: Optional[str] = None
    
    def visit_Import(self, node: ast.Import):
        """Extract import statements"""
        for name in node.names:
            self.imports.append(name.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Extract from imports"""
        module = node.module or ''
        for name in node.names:
            self.imports.append(f"{module}.{name.name}")
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class definitions and hierarchy"""
        prev_class = self.current_class
        self.current_class = node.name
        
        class_info = {
            'name': node.name,
            'bases': [base.id for base in node.bases if isinstance(base, ast.Name)],
            'methods': []
        }
        
        # Visit class body
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                class_info['methods'].append(item.name)
                
        self.class_hierarchy.append(class_info)
        self.generic_visit(node)
        self.current_class = prev_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract function definitions"""
        if self.target_line is None or (
            hasattr(node, 'lineno') and 
            abs(node.lineno - self.target_line) < 10
        ):
            self.functions.append(node.name)
        self.generic_visit(node)

@dataclass
class RepositoryAnalysis:
    """Complete repository analysis results"""
    codebase_understanding: Dict[str, Any]
    discovered_modules: List[str]
    external_dependencies: List[str]
    dependency_graph: nx.DiGraph
    documentation: List[DocumentationInfo]
    functions: List[FunctionInfo]
    relationships: CodeRelationships

@dataclass 
class DocstringInfo:
    """Information about a docstring"""
    type: Literal['module', 'class', 'function']
    name: Optional[str] = None
    content: str = ""
    lineno: int = 0

class DocstringVisitor(ast.NodeVisitor):
    """AST visitor for collecting docstrings"""
    def __init__(self):
        self.docstrings: List[DocstringInfo] = []

    def visit_Module(self, node):
        if ast.get_docstring(node):
            self.docstrings.append(DocstringInfo(
                type='module',
                content=ast.get_docstring(node),
                lineno=node.body[0].lineno if node.body else 0
            ))
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        if ast.get_docstring(node):
            self.docstrings.append(DocstringInfo(
                type='class',
                name=node.name,
                content=ast.get_docstring(node),
                lineno=node.lineno
            ))
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if ast.get_docstring(node):
            self.docstrings.append(DocstringInfo(
                type='function', 
                name=node.name,
                content=ast.get_docstring(node),
                lineno=node.lineno
            ))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Handle async functions the same way as regular functions"""
        self.visit_FunctionDef(node)

@dataclass
class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor for calculating code complexity metrics"""
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    halstead_metrics: int = 0
    
    # Halstead metrics components
    operators: Set[str] = field(default_factory=set)
    operands: Set[str] = field(default_factory=set)
    total_operators: int = 0
    total_operands: int = 0
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition"""
        self.cyclomatic_complexity += 1  # Base complexity
        self.cognitive_complexity += self._get_cognitive_complexity(node)
        self.generic_visit(node)
    
    def visit_If(self, node: ast.If):
        """Visit if statement"""
        self.cyclomatic_complexity += 1
        self.operators.add('if')
        self.total_operators += 1
        self.generic_visit(node)
    
    def visit_While(self, node: ast.While):
        """Visit while loop"""
        self.cyclomatic_complexity += 1
        self.operators.add('while')
        self.total_operators += 1
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For):
        """Visit for loop"""
        self.cyclomatic_complexity += 1
        self.operators.add('for')
        self.total_operators += 1
        self.generic_visit(node)
    
    def visit_Try(self, node: ast.Try):
        """Visit try block"""
        self.cyclomatic_complexity += len(node.handlers) + len(node.finalbody)
        self.operators.add('try')
        self.total_operators += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node: ast.BoolOp):
        """Visit boolean operation"""
        self.cyclomatic_complexity += len(node.values) - 1
        self.operators.add('bool_op')
        self.total_operators += 1
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        """Visit variable name"""
        self.operands.add(node.id)
        self.total_operands += 1
        self.generic_visit(node)
    
    def visit_Num(self, node: ast.Num):
        """Visit number"""
        self.operands.add(str(node.n))
        self.total_operands += 1
        self.generic_visit(node)
    
    def visit_Str(self, node: ast.Str):
        """Visit string"""
        self.operands.add(node.s)
        self.total_operands += 1
        self.generic_visit(node)
    
    def _get_cognitive_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity for a node"""
        complexity = 0
        nesting_level = 0
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += (1 + nesting_level)
                nesting_level += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
                
        return complexity
    
    def compute_halstead(self):
        """Compute Halstead complexity metrics"""
        n1 = len(self.operators)  # Unique operators
        n2 = len(self.operands)   # Unique operands
        N1 = self.total_operators # Total operators
        N2 = self.total_operands  # Total operands
        
        if n1 > 0 and n2 > 0:
            # Program vocabulary: n = n1 + n2
            vocabulary = n1 + n2
            # Program length: N = N1 + N2
            length = N1 + N2
            # Volume: V = N * log2(n)
            volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
            
            self.halstead_metrics = int(volume)
        else:
            self.halstead_metrics = 0

@dataclass
class TestCoverageResult:
    """Test coverage analysis results"""
    total_lines: int = 0
    covered_lines: int = 0
    coverage_percent: float = 0.0
    uncovered_lines: List[int] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)

@dataclass
class DocumentationQuality:
    """Documentation quality metrics"""
    has_docstring: bool = False
    docstring_lines: int = 0
    docstring_coverage: float = 0.0  # Percentage of documented elements
    missing_docs: List[str] = field(default_factory=list)
    style_compliance: float = 0.0    # Compliance with documentation style

@dataclass
class CodeQualityMetrics:
    """Code quality analysis results"""
    complexity: Dict[str, int]
    maintainability: Dict[str, float]
    test_coverage: TestCoverageResult
    documentation: DocumentationQuality
    style_score: float = 0.0

@dataclass
class AnalysisCache:
    """Cache for analysis results"""
    key: str
    data: Any
    timestamp: float
    ttl: Optional[int] = None

@dataclass
class FrameworkInfo:
    """Information about detected frameworks"""
    name: str
    version: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    confidence: float = 0.0

@dataclass
class FileAnalysisResult:
    """Results from analyzing a single file"""
    file_path: str
    language: str
    content: str
    ast: Optional[Any] = None
    imports: List[str] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    docstrings: List[DocstringInfo] = field(default_factory=list)
    metrics: Optional[CodeQualityMetrics] = None

@dataclass
class DependencyInfo:
    """Information about a project dependency"""
    name: str
    version: Optional[str] = None
    type: Literal['direct', 'dev', 'optional'] = 'direct'
    source: str = ""  # requirements.txt, setup.py, etc.
    constraints: List[str] = field(default_factory=list)

@dataclass
class StyleViolation:
    """Code style violation information"""
    line: int
    column: int
    code: str
    message: str
    severity: Literal['error', 'warning', 'info'] = 'warning'

@dataclass
class StyleAnalysisResult:
    """Results from style analysis"""
    violations: List[StyleViolation] = field(default_factory=list)
    style_guide: str = "PEP8"
    score: float = 100.0
    suggestions: List[str] = field(default_factory=list)

@dataclass
class SecurityIssue:
    """Security issue information"""
    type: str
    severity: Literal['critical', 'high', 'medium', 'low']
    file_path: str
    line: int
    description: str
    recommendation: str
    cwe_id: Optional[int] = None

@dataclass
class SecurityAnalysisResult:
    """Results from security analysis"""
    issues: List[SecurityIssue] = field(default_factory=list)
    scan_timestamp: float = field(default_factory=time.time)
    risk_score: float = 0.0

@dataclass
class PerformanceMetrics:
    """Code performance metrics"""
    time_complexity: str = "O(1)"  # Big O notation
    space_complexity: str = "O(1)"
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    io_operations: int = 0

@dataclass
class APIEndpoint:
    """API endpoint information"""
    path: str
    method: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    response_type: str = ""
    docstring: Optional[str] = None
    authentication: bool = False

@dataclass
class APIDocumentation:
    """API documentation information"""
    endpoints: List[APIEndpoint] = field(default_factory=list)
    base_url: Optional[str] = None
    version: str = "1.0.0"
    auth_methods: List[str] = field(default_factory=list)

@dataclass
class TestInfo:
    """Test case information"""
    name: str
    file_path: str
    type: Literal['unit', 'integration', 'e2e'] = 'unit'
    fixtures: List[str] = field(default_factory=list)
    assertions: int = 0
    coverage: float = 0.0

@dataclass
class ModuleInfo:
    """Information about a Python module"""
    name: str
    file_path: str
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    is_package: bool = False
    dependencies: List[DependencyInfo] = field(default_factory=list)

@dataclass
class ClassInfo:
    """Information about a class"""
    name: str
    file_path: str
    bases: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_dataclass: bool = False
    metrics: Optional[CodeQualityMetrics] = None

@dataclass
class ImportInfo:
    """Information about an import statement"""
    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    is_from: bool = False
    line_number: int = 0

@dataclass
class AnalysisContext:
    """Context for analysis operations"""
    repository: RepositoryInfo
    current_file: Optional[str] = None
    cache_enabled: bool = True
    analysis_depth: Literal['basic', 'detailed', 'full'] = 'detailed'
    include_metrics: bool = True
    max_file_size: int = 1024 * 1024  # 1MB default

@dataclass
class AnalysisError:
    """Error information from analysis"""
    error_type: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    traceback: Optional[str] = None
    severity: Literal['critical', 'error', 'warning', 'info'] = 'error'

@dataclass
class AnalysisStats:
    """Statistics about the analysis process"""
    start_time: float
    end_time: Optional[float] = None
    files_processed: int = 0
    errors_encountered: List[AnalysisError] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0
    total_lines_analyzed: int = 0

@dataclass
class GraphNode:
    """Neo4j graph node representation"""
    id: str
    labels: List[str]
    properties: Dict[str, Any]
    relationships: List['GraphRelationship'] = field(default_factory=list)

@dataclass
class GraphRelationship:
    """Neo4j graph relationship representation"""
    type: str
    start_node: 'GraphNode'
    end_node: 'GraphNode'
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RepositoryState:
    """Repository analysis state"""
    url: str
    status: Literal['pending', 'analyzing', 'completed', 'failed']
    last_update: float
    progress: float = 0.0
    current_operation: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class AnalysisSession:
    """Analysis session information"""
    session_id: str
    repositories: List[RepositoryInfo]
    start_time: float
    last_active: float
    context: AnalysisContext
    stats: AnalysisStats
    cache_enabled: bool = True

@dataclass
class CodeSnippet:
    """Code snippet with metadata"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    embedding: Optional[np.ndarray] = None
    context: Optional[Dict[str, Any]] = None

@dataclass
class AnalysisConfig:
    """Configuration for analysis operations"""
    max_file_size: int = 1024 * 1024  # 1MB
    ignore_patterns: List[str] = field(default_factory=lambda: [
        '__pycache__', 
        '*.pyc', 
        '.git'
    ])
    analyze_dependencies: bool = True
    analyze_docs: bool = True
    analyze_tests: bool = True
    depth: Literal['shallow', 'normal', 'deep'] = 'normal'

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    pg_conn_string: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    redis_host: str = 'localhost'
    redis_port: int = 6379
    use_cache: bool = True

@dataclass
class GraphQuery:
    """Neo4j graph query information"""
    query: str
    params: Dict[str, Any] = field(default_factory=dict)
    result_type: Literal['node', 'relationship', 'path', 'value'] = 'node'
    limit: Optional[int] = None

@dataclass
class AnalysisProgress:
    """Analysis progress tracking"""
    total_files: int = 0
    processed_files: int = 0
    current_file: Optional[str] = None
    stage: str = 'initializing'
    start_time: float = field(default_factory=time.time)
    estimated_completion: Optional[float] = None

@dataclass
class ParseResult:
    """Result from code parsing"""
    ast: Optional[Any]
    semantic: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    success: bool = True

@dataclass
class AnalysisFilter:
    """Filters for analysis operations"""
    file_types: List[str] = field(default_factory=lambda: ['.py', '.md', '.rst'])
    max_file_size: int = 1024 * 1024  # 1MB
    exclude_patterns: List[str] = field(default_factory=lambda: [
        '__pycache__',
        '*.pyc',
        '.git',
        'venv',
        'node_modules'
    ])
    include_tests: bool = True
    include_docs: bool = True

@dataclass
class AnalysisMetadata:
    """Metadata about analysis process"""
    tool_version: str
    timestamp: float = field(default_factory=time.time)
    duration: float = 0.0
    files_analyzed: int = 0
    total_lines: int = 0
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RepositoryMetrics:
    """Repository-wide metrics"""
    total_files: int = 0
    total_lines: int = 0
    code_to_comment_ratio: float = 0.0
    avg_complexity: float = 0.0
    test_coverage: float = 0.0
    documentation_coverage: float = 0.0
    maintainability_index: float = 0.0

@dataclass
class AnalysisRequest:
    """Analysis request parameters"""
    repository_url: str
    branch: str = 'main'
    depth: Literal['shallow', 'normal', 'deep'] = 'normal'
    filters: AnalysisFilter = field(default_factory=AnalysisFilter)
    force_update: bool = False
    cache_ttl: Optional[int] = 3600

@dataclass
class AnalysisResponse:
    """Analysis response container"""
    request: AnalysisRequest
    result: Union[RepositoryAnalysis, None]
    metadata: AnalysisMetadata
    errors: List[AnalysisError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class QueryResponse:
    """Response to a repository query"""
    response: str
    confidence: float = 0.0
    context_used: Dict[str, Any] = field(default_factory=dict)
    relevant_code: Optional[str] = None
    documentation_matches: List[str] = field(default_factory=list)

@dataclass
class AIAgent:
    """AI Agent configuration and state"""
    codebase_understanding: Optional[Dict[str, Any]] = None
    discovered_modules: List[str] = field(default_factory=list)
    external_dependencies: List[str] = field(default_factory=list)
    dependency_graph: Any = field(default_factory=nx.DiGraph)
    current_repo: Optional[str] = None