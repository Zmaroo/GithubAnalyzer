"""Models for code-specific analysis."""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from tree_sitter import Node, Tree

from GithubAnalyzer.models.core.ast import ParseResult
from GithubAnalyzer.models.analysis.results import BaseAnalysisResult, BaseMetrics

@dataclass
class CodeMetrics(BaseMetrics):
    """Code-specific metrics."""
    cyclomatic: int = 0
    cognitive: int = 0
    maintainability: float = 0.0
    halstead: Dict[str, float] = field(default_factory=dict)
    complexity: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get code metrics summary."""
        base_summary = super().get_summary()
        base_summary.update({
            'cyclomatic': self.cyclomatic,
            'cognitive': self.cognitive,
            'maintainability': self.maintainability,
            'halstead': self.halstead,
            'complexity_score': sum(self.complexity.values()) if self.complexity else 0
        })
        return base_summary

@dataclass
class CodeAnalysisResult(BaseAnalysisResult[CodeMetrics]):
    """Result of code analysis with AST and metrics."""
    language: str
    file_path: str
    parse_result: Optional[ParseResult] = None
    node_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: CodeMetrics = field(default_factory=CodeMetrics)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    graph_metrics: Optional[Dict[str, Any]] = None
    semantic_data: Optional[Dict[str, Any]] = None
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get code analysis summary."""
        base_summary = super().get_analysis_summary()
        base_summary.update({
            'structure': self.parse_result.get_structure() if self.parse_result else '',
            'metrics': self.metrics.get_summary() if self.metrics else {},
            'has_graph_data': bool(self.graph_metrics),
            'has_semantic_data': bool(self.semantic_data)
        })
        return base_summary
        
    def get_complexity_metrics(self) -> Dict[str, Any]:
        """Get code complexity metrics."""
        if not self.metrics:
            return {}
        return {
            'cyclomatic': self.metrics.cyclomatic,
            'cognitive': self.metrics.cognitive,
            'halstead': self.metrics.halstead,
            'maintainability': self.metrics.maintainability,
            'complexity': self.metrics.complexity
        }
        
    def get_semantic_metrics(self) -> Dict[str, Any]:
        """Get semantic analysis metrics."""
        if not self.semantic_data:
            return {}
        return {
            'similarity_scores': self.semantic_data.get('similarity', {}),
            'related_components': self.semantic_data.get('related', []),
            'documentation_matches': self.semantic_data.get('documentation', [])
        }
        
    def get_graph_metrics(self) -> Dict[str, Any]:
        """Get graph analysis metrics."""
        if not self.graph_metrics:
            return {}
        return {
            'centrality': self.graph_metrics.get('centrality', {}),
            'community': self.graph_metrics.get('community', {}),
            'paths': self.graph_metrics.get('paths', [])
        }

@dataclass
class BatchAnalysisResult:
    """Result of analyzing multiple code files."""
    results: List[CodeAnalysisResult]
    global_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get batch analysis summary."""
        languages = set(r.language for r in self.results)
        return {
            'file_count': len(self.results),
            'languages': list(languages),
            'total_nodes': sum(r.node_count for r in self.results),
            'global_metrics': self.global_metrics
        }
        
    def get_language_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics grouped by language."""
        stats = {}
        for result in self.results:
            if result.language not in stats:
                stats[result.language] = {
                    'file_count': 0,
                    'node_count': 0,
                    'complexity': {
                        'cyclomatic': 0,
                        'cognitive': 0
                    }
                }
            lang_stats = stats[result.language]
            lang_stats['file_count'] += 1
            lang_stats['node_count'] += result.node_count
            metrics = result.get_complexity_metrics()
            lang_stats['complexity']['cyclomatic'] += metrics.get('cyclomatic', 0)
            lang_stats['complexity']['cognitive'] += metrics.get('cognitive', 0)
        return stats 