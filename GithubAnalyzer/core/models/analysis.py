from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .code import ModuleInfo, CodeRelationships

@dataclass
class AnalysisResult:
    modules: List[ModuleInfo]
    relationships: CodeRelationships
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

@dataclass
class AnalysisContext:
    repository: str
    current_file: Optional[str] = None
    cache_enabled: bool = True

@dataclass
class AnalysisProgress:
    total_files: int = 0
    processed_files: int = 0
    current_file: Optional[str] = None 