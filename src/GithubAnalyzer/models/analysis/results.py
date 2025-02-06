"""Base models for analysis results."""
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar

from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')  # Type variable for metrics

@dataclass
class BaseMetrics:
    """Base class for all metrics."""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metrics."""
        logger.debug("Base metrics initialized", extra={
            'context': {
                'operation': 'initialization',
                'metric_count': len(self.raw_data)
            }
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        summary = {'raw_data': self.raw_data}
        logger.debug("Generated metrics summary", extra={
            'context': {
                'operation': 'get_summary',
                'summary': summary
            }
        })
        return summary

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

    def __post_init__(self):
        """Initialize analysis result."""
        logger.debug("Base analysis result initialized", extra={
            'context': {
                'operation': 'initialization',
                'has_metrics': self.metrics is not None,
                'error_count': len(self.errors),
                'warning_count': len(self.warnings),
                'metadata_count': len(self.metadata)
            }
        })

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        summary = {
            'language': self.language,
            'file_path': self.file_path,
            'node_count': self.node_count,
            'metadata': self.metadata,
            'has_metrics': self.metrics is not None,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
        logger.debug("Generated analysis summary", extra={
            'context': {
                'operation': 'get_summary',
                'summary': summary
            }
        })
        return summary

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        logger.warning("Added error to analysis result", extra={
            'context': {
                'operation': 'add_error',
                'error': error,
                'error_count': len(self.errors)
            }
        })

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
        logger.warning("Added warning to analysis result", extra={
            'context': {
                'operation': 'add_warning',
                'warning': warning,
                'warning_count': len(self.warnings)
            }
        })

    def update_metadata(self, key: str, value: Any) -> None:
        """Update metadata."""
        self.metadata[key] = value
        logger.debug("Updated analysis metadata", extra={
            'context': {
                'operation': 'update_metadata',
                'key': key,
                'metadata_count': len(self.metadata)
            }
        })

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