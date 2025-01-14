"""Analysis models and error definitions."""

from dataclasses import dataclass
from typing import Dict, List

from ..core.module import Module, ModuleMetadata


class AnalysisError(Exception):
    """Error raised during analysis operations."""


@dataclass
class CodeAnalysis:
    """Code analysis results."""

    module: Module
    metrics: Dict[str, float]
    issues: List[str]
    suggestions: List[str]


@dataclass
class AnalysisResult:
    """Analysis result container."""

    analyses: List[CodeAnalysis]
    summary: Dict[str, str]
    timestamp: float
