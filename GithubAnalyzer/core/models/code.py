from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class FunctionInfo:
    name: str
    docstring: Optional[str] = None
    args: List[str] = field(default_factory=list)
    returns: Optional[str] = None
    start_line: int = 0
    end_line: int = 0

@dataclass
class ClassInfo:
    name: str
    docstring: Optional[str] = None
    methods: List[FunctionInfo] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)

@dataclass
class ModuleInfo:
    path: str
    imports: List[str] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)

@dataclass
class CodeRelationships:
    imports: Dict[str, List[str]] = field(default_factory=dict)
    calls: Dict[str, List[str]] = field(default_factory=dict)
    inherits: Dict[str, List[str]] = field(default_factory=dict) 