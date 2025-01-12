from typing import Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from .utils import setup_logger

logger = setup_logger(__name__)

class CodeEmbeddingGenerator:
    """Centralized embedding generation for code analysis"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, neo4j_connection=None):
        if not hasattr(self, 'initialized'):
            # Initialize models
            self.model = SentenceTransformer('microsoft/codebert-base')
            self.structure_model = SentenceTransformer('microsoft/graphcodebert-base')
            self.semantic_model = SentenceTransformer('microsoft/unixcoder-base')
            self.doc_model = SentenceTransformer('all-mpnet-base-v2')
            
            # Store Neo4j connection for graph embeddings
            self.neo4j = neo4j_connection
            self.initialized = True
    
    def generate_embeddings(self, code_snippet: str, context: Dict[str, Any] = None, code_id: Optional[str] = None) -> Dict[str, np.ndarray]:
        """Generate comprehensive embeddings including code, structure, semantic, and graph context"""
        try:
            if context is None:
                context = {}
                
            embeddings = {
                'code_vector': self.model.encode(code_snippet),
                'structure': self._generate_structure_embedding(code_snippet),
                'semantic': self._generate_semantic_embedding(code_snippet, context),
                'documentation': self._generate_doc_embedding(code_snippet)
            }
            
            # Add graph embeddings if Neo4j is available and code_id is provided
            if self.neo4j and code_id:
                graph_embedding = self._generate_graph_embedding(code_id)
                if graph_embedding is not None:
                    embeddings['graph'] = graph_embedding
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return {}

    def _generate_structure_embedding(self, code: str) -> np.ndarray:
        """Generate embeddings focused on code structure"""
        try:
            return self.structure_model.encode(code)
        except Exception as e:
            logger.error(f"Error generating structure embedding: {e}")
            return np.array([])

    def _generate_semantic_embedding(self, code: str, context: Dict[str, Any]) -> np.ndarray:
        """Generate embeddings focused on semantic meaning"""
        try:
            semantic_context = [
                code,
                context.get('docstring', ''),
                context.get('function_name', ''),
                context.get('class_name', '')
            ]
            return self.semantic_model.encode(' '.join(semantic_context))
        except Exception as e:
            logger.error(f"Error generating semantic embedding: {e}")
            return np.array([])

    def _generate_doc_embedding(self, code: str) -> np.ndarray:
        """Generate embeddings for documentation"""
        try:
            return self.doc_model.encode(code)
        except Exception as e:
            logger.error(f"Error generating documentation embedding: {e}")
            return np.array([])

    def _generate_graph_embedding(self, code_id: str) -> Optional[np.ndarray]:
        """Generate embeddings that incorporate graph structure"""
        try:
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
                
                record = result.single()
                return np.array(record['embedding']) if record else None
        except Exception as e:
            logger.error(f"Error generating graph embedding: {e}")
            return None

    def generate_contextual_embedding(self, code: str, context: Dict[str, Any]) -> np.ndarray:
        """Generate context-aware embeddings"""
        try:
            context_str = ' '.join([
                str(context.get('imports', [])),
                str(context.get('file_path', '')),
                str(context.get('project_style', [])),
                str(context.get('common_patterns', []))
            ])
            return self.semantic_model.encode(code + ' ' + context_str)
        except Exception as e:
            logger.error(f"Error generating contextual embedding: {e}")
            return np.array([]) 