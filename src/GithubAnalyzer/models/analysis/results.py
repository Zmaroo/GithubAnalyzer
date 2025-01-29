"""Base models for analysis results."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, TypeVar, Generic

T = TypeVar('T')  # Type variable for metrics

@dataclass
class BaseMetrics:
    """Base class for all metrics."""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            'has_data': bool(self.raw_data),
            'metric_count': len(self.raw_data)
        }

@dataclass
class BaseAnalysisResult(Generic[T]):
    """Base class for all analysis results."""
    language: str
    file_path: str
    node_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: T = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        return {
            'language': self.language,
            'file_path': self.file_path,
            'node_count': self.node_count,
            'metadata': self.metadata,
            'has_metrics': self.metrics is not None,
            'has_errors': bool(self.errors),
            'has_warnings': bool(self.warnings)
        }

@dataclass
class AnalysisMetrics(BaseMetrics):
    """Common metrics for general analysis."""
    quality: Dict[str, float] = field(default_factory=dict)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        base_summary = super().get_summary()
        base_summary.update({
            'quality_score': sum(self.quality.values()) / len(self.quality) if self.quality else 0,
            'dependency_count': len(self.dependencies)
        })
        return base_summary

@dataclass
class AnalysisResult(BaseAnalysisResult[AnalysisMetrics]):
    """General analysis result with basic metrics."""
    metrics: AnalysisMetrics = field(default_factory=AnalysisMetrics)
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get enhanced analysis summary."""
        base_summary = super().get_analysis_summary()
        if self.metrics:
            base_summary['metrics'] = self.metrics.get_summary()
        return base_summary 