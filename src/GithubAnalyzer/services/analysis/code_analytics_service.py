"""Service for advanced code analytics using graph algorithms."""
from typing import Dict, List, Any, Optional

from GithubAnalyzer.services.core.database.neo4j_service import Neo4jService
from GithubAnalyzer.services.core.database.postgres_service import PostgresService
from GithubAnalyzer.models.core.database import GraphAnalytics
from GithubAnalyzer.models.analysis.code_analysis import CodeAnalysisResult, BatchAnalysisResult
from GithubAnalyzer.models.core.ast import ParseResult

class CodeAnalyticsService:
    """Service for advanced code analytics."""
    
    def __init__(self):
        """Initialize analytics service."""
        self._neo4j = Neo4jService()
        self._postgres = PostgresService()
        
    def analyze_code_structure(self, repo_id: str) -> GraphAnalytics:
        """Analyze code structure using advanced graph algorithms.
        
        This method combines multiple graph analytics approaches:
        1. Dependency Analysis (PageRank, Betweenness)
        2. Code Pattern Similarity
        3. Community Detection
        4. Path Analysis
        
        Args:
            repo_id: Repository identifier
            
        Returns:
            GraphAnalytics containing comprehensive analysis results
        """
        # 1. Analyze dependencies
        dependencies = self._neo4j.analyze_code_dependencies(repo_id)
        
        # 2. Find similar patterns across the codebase
        similar_patterns = {}
        with self._postgres as pg:
            files = pg.get_repository_files(repo_id)
            for file_path in files:
                patterns = self._neo4j.find_similar_code_patterns(file_path)
                if patterns:
                    similar_patterns[file_path] = patterns
        
        # 3. Detect code communities
        communities = self._neo4j.detect_code_communities(repo_id)
        
        # 4. Analyze critical paths
        critical_functions = dependencies['central_components']
        paths = []
        if len(critical_functions) >= 2:
            for i in range(len(critical_functions) - 1):
                start_func = critical_functions[i]['name']
                end_func = critical_functions[i + 1]['name']
                paths.extend(
                    self._neo4j.find_code_paths(start_func, end_func, repo_id)
                )
        
        # Create GraphAnalytics model
        return GraphAnalytics(
            central_components=dependencies['central_components'],
            critical_paths=paths,
            communities=communities,
            similarity_scores={
                file_path: sum(p['similarity'] for p in patterns) / len(patterns)
                for file_path, patterns in similar_patterns.items()
            }
        )
        
    def get_code_metrics(self, repo_id: str) -> CodeAnalysisResult:
        """Get comprehensive code metrics using graph analytics.
        
        This method combines various metrics:
        1. Complexity metrics from AST analysis
        2. Centrality metrics from graph analysis
        3. Community metrics from clustering
        
        Args:
            repo_id: Repository identifier
            
        Returns:
            CodeAnalysisResult containing various code metrics
        """
        # Get graph analytics
        graph_analytics = self.analyze_code_structure(repo_id)
        
        # Convert to metrics format
        graph_metrics = {
            'centrality': {
                comp['name']: comp['score']
                for comp in graph_analytics.central_components[:5]
            },
            'community': {
                f'community_{i}': members
                for i, members in enumerate(graph_analytics.communities.values())
            },
            'paths': graph_analytics.critical_paths
        }
        
        # Get repository-level metrics
        complexity_metrics = {
            'central_components': len(graph_analytics.central_components),
            'critical_paths': len(graph_analytics.critical_paths),
            'communities': len(graph_analytics.communities),
            'avg_community_size': (
                sum(len(c) for c in graph_analytics.communities.values()) / 
                len(graph_analytics.communities) if graph_analytics.communities else 0
            )
        }
        
        # Create a dummy ParseResult for repository-level analysis
        parse_result = ParseResult(
            tree=None,
            language="repository",
            is_valid=True,
            functions=[],
            classes=[],
            imports=[]
        )
        
        return CodeAnalysisResult(
            language="repository",
            file_path=f"repo:{repo_id}",
            parse_result=parse_result,
            complexity_metrics=complexity_metrics,
            graph_metrics=graph_metrics
        )
        
    def get_batch_analysis(self, repo_id: str) -> BatchAnalysisResult:
        """Get batch analysis for an entire repository.
        
        Args:
            repo_id: Repository identifier
            
        Returns:
            BatchAnalysisResult containing analysis of all files
        """
        with self._postgres as pg:
            files = pg.get_repository_files(repo_id)
            results = []
            
            for file_path in files:
                # Get code analysis
                analysis = self._analyze_file(repo_id, file_path)
                if analysis:
                    results.append(analysis)
            
            # Get global metrics from graph analysis
            repo_analysis = self.get_code_metrics(repo_id)
            
            return BatchAnalysisResult(
                results=results,
                global_metrics=repo_analysis.get_analysis_summary()
            )
            
    def _analyze_file(self, repo_id: str, file_path: str) -> Optional[CodeAnalysisResult]:
        """Analyze a single file.
        
        Args:
            repo_id: Repository identifier
            file_path: Path to the file
            
        Returns:
            CodeAnalysisResult if analysis successful, None otherwise
        """
        with self._postgres as pg:
            snippet = pg.get_code_snippet(repo_id, file_path)
            if not snippet or not snippet.ast_data:
                return None
            
            # Create ParseResult from AST data
            parse_result = ParseResult(
                tree=None,  # We don't have the tree object here
                language=snippet.language,
                is_valid=snippet.syntax_valid,
                functions=snippet.get_functions(),
                classes=snippet.get_classes(),
                imports=[]  # We should add import extraction
            )
            
            # Get graph metrics
            graph_analytics = self.analyze_code_structure(repo_id)
            graph_metrics = {
                'centrality': {
                    comp['name']: comp['score']
                    for comp in graph_analytics.central_components
                    if comp.get('file_path') == file_path
                },
                'community': next(
                    (members for members in graph_analytics.communities.values()
                     if file_path in members),
                    []
                ),
                'similarity': graph_analytics.similarity_scores.get(file_path, 0.0)
            }
            
            return CodeAnalysisResult(
                language=snippet.language,
                file_path=file_path,
                parse_result=parse_result,
                node_count=len(snippet.get_functions()) + len(snippet.get_classes()),
                complexity_metrics=snippet.complexity_metrics or {},
                graph_metrics=graph_metrics
            ) 