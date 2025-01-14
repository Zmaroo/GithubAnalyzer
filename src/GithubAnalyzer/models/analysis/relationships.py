"""Code relationship models."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from ..base import BaseModel


class RelationshipType(Enum):
    """Types of relationships between code elements."""

    IMPORTS = auto()
    INHERITS = auto()
    CALLS = auto()
    USES = auto()
    CONTAINS = auto()
    DEPENDS_ON = auto()
    IMPLEMENTS = auto()
    OVERRIDES = auto()


class DependencyType(Enum):
    """Types of dependencies between code elements."""

    RUNTIME = auto()
    DEVELOPMENT = auto()
    OPTIONAL = auto()
    TEST = auto()
    BUILD = auto()


@dataclass
class CodeRelationship(BaseModel):
    """Relationship between code elements."""

    source: str
    target: str
    type: RelationshipType
    metadata: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    is_bidirectional: bool = False


@dataclass
class CodeDependency(BaseModel):
    """Dependency between code elements."""

    source: str
    target: str
    type: DependencyType
    version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_direct: bool = True
    is_dev: bool = False
    is_optional: bool = False
