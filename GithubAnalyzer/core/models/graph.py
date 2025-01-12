"""Graph analysis models"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class CentralityMetrics:
    """Centrality metrics for code components"""
    pagerank: List[Dict[str, Any]]
    betweenness: List[Dict[str, Any]]
    eigenvector: Optional[List[Dict[str, Any]]] = None

@dataclass
class CommunityDetection:
    """Community detection results"""
    modules: List[Dict[str, Any]]
    similar_components: List[Dict[str, Any]]
    
@dataclass
class PathAnalysis:
    """Path analysis results"""
    shortest_paths: List[Dict[str, Any]]
    dependency_chains: Optional[List[Dict[str, Any]]] = None

@dataclass
class CodePattern:
    """Code pattern information"""
    pattern_type: str
    components: List[str]
    confidence: float
    metrics: Dict[str, Any]

@dataclass
class RefactoringSuggestion:
    """Refactoring suggestion"""
    type: str
    components: List[str]
    reason: str
    impact: float
    difficulty: str

@dataclass
class DependencyAnalysis:
    """Dependency analysis results"""
    circular_dependencies: List[Dict[str, Any]]
    dependency_hubs: List[Dict[str, Any]]
    dependency_clusters: List[Dict[str, Any]]

@dataclass
class CodeEvolutionMetrics:
    """Code evolution metrics"""
    change_hotspots: List[Dict[str, Any]]
    cochange_patterns: List[Dict[str, Any]]
    
@dataclass
class ASTPattern:
    """AST pattern information"""
    pattern_type: str
    occurrences: int
    locations: List[Dict[str, Any]]
    complexity: float
    embedding: Optional[List[float]] = None

@dataclass
class ASTMetrics:
    """AST-based metrics"""
    ast_size: int
    max_depth: int
    avg_branching: float
    control_flow_density: float
    cyclomatic_complexity: int

@dataclass
class CombinedAnalysis:
    """Combined AST and graph analysis"""
    ast_patterns: List[ASTPattern]
    graph_patterns: List[CodePattern]
    correlated_metrics: Dict[str, float]
    complexity_hotspots: List[Dict[str, Any]]

@dataclass
class GraphAnalysisResult:
    """Complete graph analysis results"""
    centrality: CentralityMetrics
    communities: CommunityDetection
    paths: PathAnalysis
    similarity: Dict[str, List[Dict[str, Any]]]
    patterns: Optional[List[CodePattern]] = None
    dependencies: Optional[DependencyAnalysis] = None
    evolution: Optional[CodeEvolutionMetrics] = None
    refactoring_suggestions: Optional[List[RefactoringSuggestion]] = None
    ast_analysis: Optional[CombinedAnalysis] = None
    
    def get_key_components(self, limit: int = 10) -> List[str]:
        """Get most important components based on centrality"""
        return [
            item['component'] 
            for item in sorted(
                self.centrality.pagerank,
                key=lambda x: x['score'],
                reverse=True
            )[:limit]
        ]
    
    def get_similar_components(self, component: str, threshold: float = 0.5) -> List[str]:
        """Get similar components above threshold"""
        return [
            item['component2']
            for item in self.similarity
            if item['component1'] == component and item['similarity'] >= threshold
        ] 
    
    def get_critical_components(self) -> List[str]:
        """Get components that need immediate attention"""
        critical = set()
        
        # Components with high centrality
        critical.update(self.get_key_components(5))
        
        # Components in circular dependencies
        if self.dependencies:
            for group in self.dependencies.circular_dependencies:
                critical.update(group['components'])
                
        # Frequently changing components
        if self.evolution:
            for hotspot in self.evolution.change_hotspots[:5]:
                critical.add(hotspot['component'])
                
        return list(critical)
    
    def get_refactoring_priorities(self) -> List[Dict[str, Any]]:
        """Get prioritized refactoring suggestions"""
        if not self.refactoring_suggestions:
            return []
            
        return sorted(
            [s.__dict__ for s in self.refactoring_suggestions],
            key=lambda x: (x['impact'], -len(x['components'])),
            reverse=True
        ) 
    
    def get_complexity_hotspots(self) -> List[str]:
        """Get components with high combined complexity"""
        if not self.ast_analysis:
            return []
            
        return [
            spot['component']
            for spot in self.ast_analysis.complexity_hotspots
            if spot['combined_complexity'] > self.get_complexity_threshold()
        ]
    
    def get_complexity_threshold(self) -> float:
        """Calculate complexity threshold using statistics"""
        if not self.ast_analysis or not self.ast_analysis.complexity_hotspots:
            return 0.0
            
        complexities = [
            spot['combined_complexity'] 
            for spot in self.ast_analysis.complexity_hotspots
        ]
        mean = sum(complexities) / len(complexities)
        std_dev = (
            sum((x - mean) ** 2 for x in complexities) 
            / len(complexities)
        ) ** 0.5
        
        return mean + (2 * std_dev)  # Two standard deviations above mean 