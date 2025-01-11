from typing import Dict, Any
import numpy as np
from neo4j import GraphDatabase

class GraphAwareEmbeddings:
    def __init__(self, neo4j_connection):
        self.neo4j = neo4j_connection
        
    def generate_graph_enhanced_embeddings(self, code_id: str) -> np.ndarray:
        """Generate embeddings that incorporate graph structure"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (n:CodeNode {id: $code_id})
                CALL gds.fastRP.stream('code_graph', {
                    embeddingDimension: 256,
                    relationshipWeightProperty: 'weight',
                    iterationWeights: [0.8, 1.0, 1.2],
                    featureProperties: ['type', 'complexity', 'dependencies', 'usage_patterns']
                })
                YIELD nodeId, embedding
                RETURN embedding
            """, code_id=code_id)
            
            return np.array(result.single()['embedding']) 