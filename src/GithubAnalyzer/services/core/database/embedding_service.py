from transformers import AutoTokenizer, AutoModel
from typing import List, Union
import torch

class CodeEmbeddingService:
    """Service for generating code embeddings using GraphCodeBERT."""
    
    def __init__(self):
        self.model_name = "microsoft/graphcodebert-base"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        
    def initialize(self) -> None:
        """Initialize the model and tokenizer."""
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
    
    def get_embeddings(self, code_snippets: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple code snippets.
        
        Args:
            code_snippets: List of code snippets to embed.
            
        Returns:
            List of embeddings, one for each code snippet.
        """
        self.initialize()
        
        # Tokenize all snippets
        inputs = self.tokenizer(
            code_snippets,
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
        
        return embeddings.tolist()
    
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