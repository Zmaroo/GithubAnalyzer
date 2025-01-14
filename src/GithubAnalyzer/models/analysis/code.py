"""Code structure models."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..base import BaseModel


@dataclass
class ImportInfo(BaseModel):
    """Information about an import statement."""

    name: str
    alias: Optional[str] = None
    is_from_import: bool = False
    imported_names: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class FunctionInfo(BaseModel):
    """Information about a function."""

    name: str
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    is_async: bool = False
    line_number: int = 0
    complexity: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassInfo(BaseModel):
    """Information about a class."""

    name: str
    docstring: Optional[str] = None
    base_classes: List[str] = field(default_factory=list)
    methods: List[FunctionInfo] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    line_number: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
