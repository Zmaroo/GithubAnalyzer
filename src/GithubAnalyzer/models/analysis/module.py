"""Module information models."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..base import BaseModel


@dataclass
class ModuleInfo(BaseModel):
    """Information about a Python module."""

    name: str
    path: str
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    is_package: bool = False
    is_test: bool = False
