"""Module information models"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class FunctionInfo:
    """Information about a function"""
    name: str
    docstring: Optional[str] = None
    parameters: List[Dict[str, str]] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    complexity: Optional[int] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None

@dataclass
class ClassInfo:
    """Information about a class"""
    name: str
    docstring: Optional[str] = None
    methods: List[FunctionInfo] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    start_line: Optional[int] = None
    end_line: Optional[int] = None

@dataclass
class ModuleInfo:
    """Information about a Python module"""
    path: str
    imports: List[str] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    docstring: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    success: bool = True
    metrics: Dict[str, Any] = field(default_factory=dict) 