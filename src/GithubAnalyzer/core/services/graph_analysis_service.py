"""Graph analysis service using Neo4j GDS"""
from typing import Dict, Any, List, Optional
from .base_service import BaseService
from ..models.graph import (
    GraphAnalysisResult,
    CentralityMetrics,
    CommunityDetection,
    PathAnalysis
)
from ..utils.logging import setup_logger
from ..utils.performance import measure_time

logger = setup_logger(__name__)

class GraphAnalysisService(BaseService):
    """Service for graph-based code analysis using Neo4j GDS"""
    
    def _initialize(self) -> None:
        self.graph_name = "code_analysis_graph"
        self._ensure_graph_exists()

    @measure_time
    def analyze_code_structure(self, repo_url: str) -> GraphAnalysisResult:
        """Analyze code structure using graph algorithms"""
        try:
            # Project graph if not exists
            self._project_graph()
            
            return GraphAnalysisResult(
                centrality=self._compute_centrality_metrics(),
                communities=self._detect_communities(),
                paths=self._analyze_paths(),
                similarity=self._compute_node_similarity()
            )
        except Exception as e:
            logger.error(f"Error in graph analysis: {e}")
            return None

    def _project_graph(self) -> None:
        """Project graph for analysis"""
        query = """
        CALL gds.graph.project(
            $graph_name,
            ['File', 'Class', 'Function'],
            {
                IMPORTS: {
                    orientation: 'UNDIRECTED'
                },
                CALLS: {
                    orientation: 'NATURAL'
                },
                DEFINES: {
                    orientation: 'NATURAL'
                }
            }
        )
        """
        self.registry.database_service.execute_graph_query(
            query, 
            {"graph_name": self.graph_name}
        )

    def _compute_centrality_metrics(self) -> CentralityMetrics:
        """Compute various centrality metrics"""
        # PageRank for identifying important code components
        pagerank_query = """
        CALL gds.pageRank.stream($graph_name)
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).name AS component, score
        ORDER BY score DESC
        LIMIT 10
        """
        
        # Betweenness for identifying bridge components
        betweenness_query = """
        CALL gds.betweenness.stream($graph_name)
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).name AS component, score
        ORDER BY score DESC
        LIMIT 10
        """
        
        return CentralityMetrics(
            pagerank=self.registry.database_service.execute_graph_query(
                pagerank_query, 
                {"graph_name": self.graph_name}
            ),
            betweenness=self.registry.database_service.execute_graph_query(
                betweenness_query,
                {"graph_name": self.graph_name}
            )
        )

    def _detect_communities(self) -> CommunityDetection:
        """Detect code communities/modules"""
        # Louvain for detecting code modules
        louvain_query = """
        CALL gds.louvain.stream($graph_name)
        YIELD nodeId, communityId
        RETURN gds.util.asNode(nodeId).name AS component,
               communityId,
               count(*) AS community_size
        ORDER BY community_size DESC
        """
        
        # Node similarity for finding similar components
        similarity_query = """
        CALL gds.nodeSimilarity.stream($graph_name)
        YIELD node1, node2, similarity
        WHERE similarity > 0.5
        RETURN gds.util.asNode(node1).name AS component1,
               gds.util.asNode(node2).name AS component2,
               similarity
        ORDER BY similarity DESC
        LIMIT 20
        """
        
        return CommunityDetection(
            modules=self.registry.database_service.execute_graph_query(
                louvain_query,
                {"graph_name": self.graph_name}
            ),
            similar_components=self.registry.database_service.execute_graph_query(
                similarity_query,
                {"graph_name": self.graph_name}
            )
        )

    def _analyze_paths(self) -> PathAnalysis:
        """Analyze paths and dependencies"""
        # Shortest paths between components
        paths_query = """
        CALL gds.allShortestPaths.stream($graph_name)
        YIELD sourceNodeId, targetNodeId, distance
        WHERE distance < 5
        RETURN gds.util.asNode(sourceNodeId).name AS source,
               gds.util.asNode(targetNodeId).name AS target,
               distance
        ORDER BY distance
        LIMIT 20
        """
        
        return PathAnalysis(
            shortest_paths=self.registry.database_service.execute_graph_query(
                paths_query,
                {"graph_name": self.graph_name}
            )
        )

    def _compute_node_similarity(self) -> Dict[str, List[Dict[str, Any]]]:
        """Compute similarity between code components"""
        query = """
        CALL gds.nodeSimilarity.stream($graph_name, {
            similarityMetric: 'jaccard',
            degreeCutoff: 1
        })
        YIELD node1, node2, similarity
        WHERE similarity > 0.1
        RETURN gds.util.asNode(node1).name AS component1,
               gds.util.asNode(node2).name AS component2,
               similarity
        ORDER BY similarity DESC
        LIMIT 50
        """
        
        return self.registry.database_service.execute_graph_query(
            query,
            {"graph_name": self.graph_name}
        )

    def _ensure_graph_exists(self) -> None:
        """Ensure the named graph exists"""
        check_query = """
        CALL gds.graph.exists($graph_name)
        YIELD exists
        """
        result = self.registry.database_service.execute_graph_query(
            check_query,
            {"graph_name": self.graph_name}
        )
        
        if not result or not result[0]['exists']:
            self._project_graph() 

    def analyze_code_patterns(self) -> Dict[str, Any]:
        """Analyze code patterns using graph embeddings and clustering"""
        try:
            # Generate node embeddings using FastRP
            embedding_query = """
            CALL gds.fastRP.stream($graph_name, {
                embeddingDimension: 128,
                iterationWeights: [0.8, 1.0, 1.2],
                relationshipWeightProperty: 'weight'
            })
            YIELD nodeId, embedding
            RETURN gds.util.asNode(nodeId).name AS component, embedding
            """
            
            # Use K-Means for pattern detection
            clustering_query = """
            CALL gds.beta.kmeans.stream($graph_name, {
                nodeProperties: ['embedding'],
                k: 5,
                randomSeed: 42
            })
            YIELD nodeId, communityId
            RETURN gds.util.asNode(nodeId).name AS component,
                   communityId AS pattern_group
            ORDER BY pattern_group
            """
            
            return {
                'embeddings': self.registry.database_service.execute_graph_query(
                    embedding_query,
                    {"graph_name": self.graph_name}
                ),
                'patterns': self.registry.database_service.execute_graph_query(
                    clustering_query,
                    {"graph_name": self.graph_name}
                )
            }
        except Exception as e:
            logger.error(f"Error analyzing code patterns: {e}")
            return {}

    def analyze_dependency_structure(self) -> Dict[str, Any]:
        """Analyze dependency structure using graph algorithms"""
        try:
            # Strongly connected components for circular dependencies
            scc_query = """
            CALL gds.scc.stream($graph_name)
            YIELD nodeId, componentId
            WITH componentId, collect(gds.util.asNode(nodeId).name) AS components
            WHERE size(components) > 1
            RETURN componentId, components AS circular_dependency_group
            ORDER BY size(components) DESC
            """
            
            # Degree centrality for dependency hubs
            degree_query = """
            CALL gds.degree.stream($graph_name)
            YIELD nodeId, score
            RETURN gds.util.asNode(nodeId).name AS component,
                   score AS dependency_count
            ORDER BY dependency_count DESC
            LIMIT 20
            """
            
            # Triangle count for dependency clusters
            triangle_query = """
            CALL gds.triangleCount.stream($graph_name)
            YIELD nodeId, triangleCount
            WHERE triangleCount > 0
            RETURN gds.util.asNode(nodeId).name AS component,
                   triangleCount AS cluster_density
            ORDER BY cluster_density DESC
            """
            
            return {
                'circular_dependencies': self.registry.database_service.execute_graph_query(
                    scc_query,
                    {"graph_name": self.graph_name}
                ),
                'dependency_hubs': self.registry.database_service.execute_graph_query(
                    degree_query,
                    {"graph_name": self.graph_name}
                ),
                'dependency_clusters': self.registry.database_service.execute_graph_query(
                    triangle_query,
                    {"graph_name": self.graph_name}
                )
            }
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {e}")
            return {}

    def analyze_code_evolution(self, time_window: str = '30 days') -> Dict[str, Any]:
        """Analyze code evolution patterns"""
        try:
            # Temporal degree centrality
            temporal_query = """
            CALL gds.degree.stream($graph_name, {
                relationshipWeightProperty: 'timestamp',
                relationshipTypes: ['MODIFIES']
            })
            YIELD nodeId, score
            WHERE score > 0
            RETURN gds.util.asNode(nodeId).name AS component,
                   score AS change_frequency
            ORDER BY change_frequency DESC
            LIMIT 20
            """
            
            # Co-change patterns using node similarity
            cochange_query = """
            CALL gds.nodeSimilarity.stream($graph_name, {
                relationshipTypes: ['MODIFIES'],
                similarityMetric: 'overlap'
            })
            YIELD node1, node2, similarity
            WHERE similarity > 0.3
            RETURN gds.util.asNode(node1).name AS component1,
                   gds.util.asNode(node2).name AS component2,
                   similarity AS cochange_likelihood
            ORDER BY cochange_likelihood DESC
            LIMIT 30
            """
            
            return {
                'change_hotspots': self.registry.database_service.execute_graph_query(
                    temporal_query,
                    {"graph_name": self.graph_name}
                ),
                'cochange_patterns': self.registry.database_service.execute_graph_query(
                    cochange_query,
                    {"graph_name": self.graph_name}
                )
            }
        except Exception as e:
            logger.error(f"Error analyzing code evolution: {e}")
            return {}

    def get_refactoring_suggestions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate refactoring suggestions based on graph analysis"""
        try:
            # Identify highly coupled components
            coupling_query = """
            CALL gds.nodeSimilarity.stream($graph_name)
            YIELD node1, node2, similarity
            WHERE similarity > 0.7
            RETURN gds.util.asNode(node1).name AS component1,
                   gds.util.asNode(node2).name AS component2,
                   similarity AS coupling_score,
                   'high_coupling' AS refactoring_type
            ORDER BY coupling_score DESC
            LIMIT 10
            """
            
            # Identify potential abstractions using community detection
            abstraction_query = """
            CALL gds.louvain.stream($graph_name)
            YIELD nodeId, communityId
            WITH communityId, collect(gds.util.asNode(nodeId).name) AS components
            WHERE size(components) > 3
            RETURN components,
                   'potential_abstraction' AS refactoring_type
            LIMIT 10
            """
            
            return {
                'coupling_based': self.registry.database_service.execute_graph_query(
                    coupling_query,
                    {"graph_name": self.graph_name}
                ),
                'abstraction_based': self.registry.database_service.execute_graph_query(
                    abstraction_query,
                    {"graph_name": self.graph_name}
                )
            }
        except Exception as e:
            logger.error(f"Error generating refactoring suggestions: {e}")
            return {}

    def analyze_ast_patterns(self) -> Dict[str, Any]:
        """Analyze AST patterns using graph algorithms"""
        try:
            # Project AST structure to graph
            ast_projection_query = """
            CALL gds.graph.project.cypher(
                'ast_graph',
                'MATCH (n:ASTNode) RETURN id(n) AS id, labels(n) AS labels, n.type AS type',
                'MATCH (n:ASTNode)-[r:CHILD|NEXT]->(m:ASTNode) RETURN id(n) AS source, id(m) AS target, type(r) AS type'
            )
            """
            
            # Find common AST subtree patterns
            pattern_query = """
            CALL gds.beta.graphSage.stream('ast_graph', {
                featureProperties: ['type'],
                embeddingDimension: 64,
                relationshipWeightProperty: null,
                projectedFeatureDimension: 32
            })
            YIELD nodeId, embedding
            WITH gds.util.asNode(nodeId) AS node, embedding
            WHERE node.type IN ['FunctionDef', 'ClassDef', 'Call', 'Assign']
            RETURN node.type AS pattern_type,
                   node.name AS name,
                   embedding
            """
            
            # Analyze AST complexity patterns
            complexity_query = """
            MATCH (n:ASTNode)
            WHERE n.type = 'FunctionDef'
            WITH n, size((n)-[:CHILD*]->()) as ast_size,
                 size((n)-[:CHILD*]->(:If|:For|:While)) as control_flow_count
            RETURN n.name AS function_name,
                   ast_size AS complexity,
                   control_flow_count AS control_structures,
                   (1.0 * control_flow_count / ast_size) AS complexity_density
            ORDER BY complexity DESC
            LIMIT 20
            """
            
            return {
                'ast_patterns': self.registry.database_service.execute_graph_query(
                    pattern_query,
                    {"graph_name": self.graph_name}
                ),
                'complexity_analysis': self.registry.database_service.execute_graph_query(
                    complexity_query,
                    {"graph_name": self.graph_name}
                )
            }
        except Exception as e:
            logger.error(f"Error analyzing AST patterns: {e}")
            return {}

    def correlate_ast_metrics(self) -> Dict[str, Any]:
        """Correlate AST metrics with graph metrics"""
        try:
            correlation_query = """
            MATCH (n:ASTNode)-[:DEFINES]->(f:Function)
            WITH f,
                 size((n)-[:CHILD*]->()) AS ast_complexity,
                 gds.degree.stream($graph_name, {
                     nodeLabels: ['Function'],
                     relationshipTypes: ['CALLS']
                 }) AS dependency_score
            RETURN f.name AS function_name,
                   ast_complexity,
                   dependency_score,
                   (ast_complexity * dependency_score) AS combined_complexity
            ORDER BY combined_complexity DESC
            LIMIT 15
            """
            
            return self.registry.database_service.execute_graph_query(
                correlation_query,
                {"graph_name": self.graph_name}
            )
        except Exception as e:
            logger.error(f"Error correlating AST metrics: {e}")
            return {} 