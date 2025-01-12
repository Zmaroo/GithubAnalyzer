from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal

@dataclass
class DocumentationInfo:
    """Information about documentation"""
    content: str
    doc_type: Literal['docstring', 'comment', 'markdown', 'rst']
    line_number: Optional[int] = None
    scope: Optional[str] = None

@dataclass
class FunctionInfo:
    """Information about a function"""
    name: str
    docstring: Optional[str] = None
    args: List[str] = field(default_factory=list)
    returns: Optional[str] = None
    start_line: int = 0
    end_line: int = 0
    complexity: int = 0

@dataclass
class ClassInfo:
    """Information about a class"""
    name: str
    docstring: Optional[str] = None
    methods: List[FunctionInfo] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)

@dataclass
class ModuleInfo:
    """Information about a module"""
    path: str
    imports: List[str] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    documentation: List[DocumentationInfo] = field(default_factory=list)

@dataclass
class CodeRelationships:
    """Code relationship information"""
    imports: Dict[str, List[str]] = field(default_factory=dict)
    calls: Dict[str, List[str]] = field(default_factory=dict)
    inherits: Dict[str, List[str]] = field(default_factory=dict) 