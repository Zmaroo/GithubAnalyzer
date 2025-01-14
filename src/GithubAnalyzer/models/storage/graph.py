"""Graph storage models."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..base import BaseModel


@dataclass
class GraphNode(BaseModel):
    """Node in a graph database."""

    id: str
    labels: List[str]
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphRelationship(BaseModel):
    """Relationship between nodes in a graph database."""

    type: str
    start_node: GraphNode
    end_node: GraphNode
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphQuery(BaseModel):
    """Query for graph database."""

    query: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None
    database: Optional[str] = None


@dataclass
class GraphAnalysisResult(BaseModel):
    """Result of graph analysis."""

    nodes: List[GraphNode] = field(default_factory=list)
    relationships: List[GraphRelationship] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    is_successful: bool = True
