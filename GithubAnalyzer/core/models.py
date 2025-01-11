from typing import List, Optional, Set, Literal
from dataclasses import dataclass, field

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