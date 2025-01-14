"""Module models for code analysis."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import BaseModel


@dataclass
class ModuleMetadata(BaseModel):
    """Metadata for a code module."""

    name: str
    path: str
    language: str
    size: int = 0
    lines: int = 0
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    is_package: bool = False
    is_test: bool = False


class Module(BaseModel):
    """Represents a code module."""

    def __init__(self, metadata: ModuleMetadata):
        """Initialize a module with its metadata.

        Args:
            metadata: Module metadata.
        """
        super().__init__()
        self._metadata = metadata

    @property
    def name(self) -> str:
        """Get module name."""
        return self._metadata.name

    @property
    def path(self) -> str:
        """Get module path."""
        return self._metadata.path

    @property
    def language(self) -> str:
        """Get module language."""
        return self._metadata.language

    @property
    def size(self) -> int:
        """Get module size in bytes."""
        return self._metadata.size

    @property
    def lines(self) -> int:
        """Get number of lines in module."""
        return self._metadata.lines

    @property
    def imports(self) -> List[str]:
        """Get module imports."""
        return self._metadata.imports

    @property
    def functions(self) -> List[str]:
        """Get module functions."""
        return self._metadata.functions

    @property
    def classes(self) -> List[str]:
        """Get module classes."""
        return self._metadata.classes

    @property
    def dependencies(self) -> Dict[str, List[str]]:
        """Get module dependencies."""
        return self._metadata.dependencies

    @property
    def metrics(self) -> Dict[str, Any]:
        """Get module metrics."""
        return self._metadata.metrics

    @property
    def errors(self) -> List[str]:
        """Get module errors."""
        return self._metadata.errors

    @property
    def docstring(self) -> Optional[str]:
        """Get module docstring."""
        return self._metadata.docstring

    @property
    def is_package(self) -> bool:
        """Check if module is a package."""
        return self._metadata.is_package

    @property
    def is_test(self) -> bool:
        """Check if module is a test module."""
        return self._metadata.is_test
