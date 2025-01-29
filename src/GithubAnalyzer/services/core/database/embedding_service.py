try:
    from transformers import AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from typing import List, Union
from GithubAnalyzer.utils.logging import get_logger

logger = get_logger(__name__)

class CodeEmbeddingService:
    """Service for generating code embeddings using GraphCodeBERT."""
    
    def __init__(self):
        self.model_name = "microsoft/graphcodebert-base"
        # Check for M1/M2/M3 Mac Metal support first, then CUDA, then fall back to CPU
        self.device = "mps" if TORCH_AVAILABLE and torch.backends.mps.is_available() else \
                     "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self.is_available = TRANSFORMERS_AVAILABLE and TORCH_AVAILABLE
        
        if not self.is_available:
            logger.warning("Code embeddings disabled: required packages not available (transformers and/or torch)")
            
    def initialize(self) -> None:
        """Initialize the model and tokenizer."""
        if not self.is_available:
            return
            
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self.model is None:
            self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
            self.model.eval()  # Set to evaluation mode
            
    def get_embedding(self, code: str) -> List[float]:
        """Generate embedding for a code snippet.
        
        Args:
            code: The code snippet to embed.
            
        Returns:
            A list of floats representing the code embedding.
        """
        if not self.is_available:
            return [0.0] * 768  # Return zero embedding when dependencies not available
            
        if not code or not code.strip():
            logger.warning("Empty code snippet provided, returning zero embedding")
            return [0.0] * 768  # GraphCodeBERT's embedding size
            
        try:
            self.initialize()
            
            # Tokenize the code
            inputs = self.tokenizer(
                code,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use [CLS] token embedding as code representation
                embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            return embeddings[0].tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            return [0.0] * 768  # Return zero embedding on error
    
    def get_embeddings(self, code_snippets: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple code snippets.
        
        Args:
            code_snippets: List of code snippets to embed.
            
        Returns:
            List of embeddings, one for each code snippet.
        """
        if not self.is_available:
            return [[0.0] * 768] * len(code_snippets)  # Return zero embeddings when dependencies not available
            
        if not code_snippets:
            logger.warning("Empty code snippets list provided")
            return []
            
        try:
            # Filter out empty snippets
            valid_snippets = [s for s in code_snippets if s and s.strip()]
            if not valid_snippets:
                logger.warning("No valid code snippets found in list")
                return [[0.0] * 768] * len(code_snippets)  # Return zero embeddings
                
            self.initialize()
            
            # Tokenize all snippets
            inputs = self.tokenizer(
                valid_snippets,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use [CLS] token embeddings as code representations
                embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            # Map embeddings back to original snippets (including empty ones)
            result = []
            valid_idx = 0
            for snippet in code_snippets:
                if snippet and snippet.strip():
                    result.append(embeddings[valid_idx].tolist())
                    valid_idx += 1
                else:
                    result.append([0.0] * 768)  # Zero embedding for empty snippets
                    
            return result
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            return [[0.0] * 768] * len(code_snippets)  # Return zero embeddings on error
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between 0 and 1
        """
        tensor1 = torch.tensor(embedding1).unsqueeze(0)
        tensor2 = torch.tensor(embedding2).unsqueeze(0)
        
        cos = torch.nn.CosineSimilarity(dim=1)
        similarity = cos(tensor1, tensor2).item()
        
        return similarity 