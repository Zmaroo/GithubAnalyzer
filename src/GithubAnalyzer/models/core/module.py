"""Module models for code analysis."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ModuleMetadata:
    """Metadata for a code module."""

    name: str
    path: str
    language: str
    size: int
    lines: int
    imports: List[str]
    dependencies: Dict[str, List[str]]
    metrics: Dict[str, float]


class Module:
    """Represents a code module."""

    def __init__(self, metadata: ModuleMetadata):
        """Initialize a module with its metadata.

        Args:
            metadata: Module metadata.
        """
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
        """Get module size."""
        return self._metadata.size

    @property
    def lines(self) -> int:
        """Get number of lines."""
        return self._metadata.lines

    @property
    def imports(self) -> List[str]:
        """Get module imports."""
        return self._metadata.imports

    @property
    def dependencies(self) -> Dict[str, List[str]]:
        """Get module dependencies."""
        return self._metadata.dependencies

    @property
    def metrics(self) -> Dict[str, float]:
        """Get module metrics."""
        return self._metadata.metrics
