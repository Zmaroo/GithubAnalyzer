"""Query-related models for code analysis."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from tree_sitter import Node

from GithubAnalyzer.models.core.base_model import BaseModel


@dataclass
class QueryStats(BaseModel):
    """Statistics about a query execution."""
    pattern_count: int = 0
    capture_count: int = 0
    match_limit: int = 0
    execution_time_ms: float = 0.0
    unrooted_patterns: List[int] = field(default_factory=list)

@dataclass
class QueryCapture(BaseModel):
    """A captured node from a query."""
    name: str
    node: Node
    pattern_index: int

@dataclass
class QueryResult(BaseModel):
    """Result of executing a query."""
    captures: List[QueryCapture] = field(default_factory=list)
    stats: Optional[QueryStats] = None
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)

@dataclass
class QueryPattern(BaseModel):
    """A tree-sitter query pattern."""
    pattern: str
    name: str
    language: str
    type: str = "query"
    is_optimized: bool = False

@dataclass
class QueryExecutor(BaseModel):
    """Executor for tree-sitter queries."""
    match_limit: int = 1000
    timeout_micros: int = 0
    byte_range: Optional[tuple[int, int]] = None
    point_range: Optional[tuple[tuple[int, int], tuple[int, int]]] = None

@dataclass
class QueryOptimizationSettings(BaseModel):
    """Settings for query optimization."""
    match_limit: Optional[int] = None
    timeout_micros: Optional[int] = None
    byte_range: Optional[tuple[int, int]] = None
    point_range: Optional[tuple[tuple[int, int], tuple[int, int]]] = None 