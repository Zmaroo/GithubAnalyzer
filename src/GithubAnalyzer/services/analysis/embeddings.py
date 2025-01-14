import logging
from typing import Any, Dict, List, Optional

import numpy as np
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

from .code_utils import preprocess_code


class EmbeddingService:
    """Service for generating and managing code embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize the embedding service with a specific model."""
        self.model = SentenceTransformer(model_name)
        self.db = None

    def connect_db(self, uri: str, user: str, password: str) -> bool:
        """Connect to Neo4j database."""
        try:
            self.db = GraphDatabase.driver(uri, auth=(user, password))
            return True
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            return False

    def generate_embeddings(
        self, code: str, context: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """Generate embeddings for code with optional context."""
        try:
            processed_code = preprocess_code(code)
            if context:
                processed_code = (
                    f"{processed_code} {' '.join(str(v) for v in context.values())}"
                )
            return self.model.encode([processed_code])[0]
        except Exception as e:
            logging.error(f"Failed to generate embeddings: {e}")
            return np.zeros(384)  # Default embedding size for all-MiniLM-L6-v2

    def store_embeddings(self, code_id: str, embeddings: np.ndarray) -> bool:
        """Store embeddings in the database."""
        if not self.db:
            return False

        try:
            query = "MERGE (c:Code {id: $code_id}) " "SET c.embeddings = $embeddings"
            with self.db.session() as session:
                session.run(query, code_id=code_id, embeddings=embeddings.tolist())
            return True
        except Exception as e:
            logging.error(f"Failed to store embeddings: {e}")
            return False

    def find_similar_code(
        self, embeddings: np.ndarray, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar code snippets using embeddings."""
        if not self.db:
            return []

        try:
            query = (
                "MATCH (c:Code) "
                "WITH c, gds.similarity.cosine(c.embeddings, $embeddings) AS similarity "
                "ORDER BY similarity DESC "
                "LIMIT $limit "
                "RETURN c.id, c.code, similarity"
            )
            with self.db.session() as session:
                result = session.run(query, embeddings=embeddings.tolist(), limit=limit)
                return [dict(record) for record in result]
        except Exception as e:
            logging.error(f"Failed to find similar code: {e}")
            return []

    def close(self) -> None:
        """Close database connection."""
        if self.db:
            self.db.close()
