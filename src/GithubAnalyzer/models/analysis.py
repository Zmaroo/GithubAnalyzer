"""Analysis models"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .module import ModuleInfo

@dataclass
class AnalysisContext:
    """Context for analysis operations"""
    repository_path: str
    current_file: Optional[str] = None
    cache_enabled: bool = True
    max_file_size: int = 1024 * 1024  # 1MB
    excluded_patterns: List[str] = field(default_factory=lambda: [
        '__pycache__',
        '.git',
        'venv',
        'node_modules'
    ])
    metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnalysisResult:
    """Result of code analysis"""
    modules: List[ModuleInfo]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    success: bool = True 