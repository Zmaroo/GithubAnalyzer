"""Service for generating code embeddings using GraphCodeBERT."""
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Union

try:
    from transformers import AutoModel, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from GithubAnalyzer.utils.logging import get_logger

# Initialize logger
logger = get_logger("database.embeddings")

@dataclass
class CodeEmbeddingService:
    """Service for generating code embeddings using GraphCodeBERT."""
    
    def __post_init__(self):
        """Initialize the embedding service."""
        self._logger = logger
        self._start_time = time.time()
        
        self._logger.debug("Initializing embedding service", extra={
            'context': {
                'module': 'embeddings',
                'thread': threading.get_ident(),
                'duration_ms': 0
            }
        })
        
        self.model_name = "microsoft/graphcodebert-base"
        # Check for M1/M2/M3 Mac Metal support first, then CUDA, then fall back to CPU
        self.device = "mps" if TORCH_AVAILABLE and torch.backends.mps.is_available() else \
                     "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self.is_available = TRANSFORMERS_AVAILABLE and TORCH_AVAILABLE
        
        if not self.is_available:
            self._log("warning", "Code embeddings disabled: required packages not available",
                     missing_packages=[
                         "transformers" if not TRANSFORMERS_AVAILABLE else None,
                         "torch" if not TORCH_AVAILABLE else None
                     ])
            
    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """Get standard context for logging.
        
        Args:
            **kwargs: Additional context key-value pairs
            
        Returns:
            Dict with standard context fields plus any additional fields
        """
        context = {
            'module': 'embeddings',
            'thread': threading.get_ident(),
            'duration_ms': (time.time() - self._start_time) * 1000,
            'device': self.device,
            'model': self.model_name,
            'is_available': self.is_available
        }
        context.update(kwargs)
        return context

    def _log(self, level: str, message: str, **kwargs) -> None:
        """Log with consistent context.
        
        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Message to log
            **kwargs: Additional context key-value pairs
        """
        context = self._get_context(**kwargs)
        getattr(self._logger, level)(message, extra={'context': context})
            
    def initialize(self) -> None:
        """Initialize the model and tokenizer."""
        if not self.is_available:
            return
            
        start_time = time.time()
        try:
            if self.tokenizer is None:
                self._log("debug", "Initializing tokenizer")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                
            if self.model is None:
                self._log("debug", "Initializing model")
                self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
                self.model.eval()  # Set to evaluation mode
                
            duration = (time.time() - start_time) * 1000
            self._log("info", "Model and tokenizer initialized successfully",
                     duration_ms=duration)
                     
        except Exception as e:
            self._log("error", "Failed to initialize model and tokenizer",
                     error=str(e))
            raise

    def get_embedding(self, code: str) -> List[float]:
        """Generate embedding for a code snippet."""
        if not self.is_available:
            self._log("warning", "Returning zero embedding - service not available")
            return [0.0] * 768  # Return zero embedding when dependencies not available
            
        if not code or not code.strip():
            self._log("warning", "Empty code snippet provided, returning zero embedding")
            return [0.0] * 768  # GraphCodeBERT's embedding size
            
        start_time = time.time()
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
            
            duration = (time.time() - start_time) * 1000
            self._log("debug", "Generated embedding successfully",
                     code_length=len(code),
                     duration_ms=duration)
                     
            return embeddings[0].tolist()
            
        except Exception as e:
            self._log("error", "Failed to generate embedding",
                     code_length=len(code),
                     error=str(e))
            return [0.0] * 768  # Return zero embedding on error

    def get_embeddings(self, code_snippets: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple code snippets."""
        if not self.is_available:
            self._log("warning", "Returning zero embeddings - service not available",
                     snippet_count=len(code_snippets))
            return [[0.0] * 768] * len(code_snippets)
            
        if not code_snippets:
            self._log("warning", "Empty code snippets list provided")
            return []
            
        start_time = time.time()
        try:
            # Filter out empty snippets
            valid_snippets = [s for s in code_snippets if s and s.strip()]
            if not valid_snippets:
                self._log("warning", "No valid code snippets found in list",
                         total_snippets=len(code_snippets))
                return [[0.0] * 768] * len(code_snippets)
                
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
                    
            duration = (time.time() - start_time) * 1000
            self._log("debug", "Generated embeddings successfully",
                     total_snippets=len(code_snippets),
                     valid_snippets=len(valid_snippets),
                     duration_ms=duration)
                     
            return result
            
        except Exception as e:
            self._log("error", "Failed to generate embeddings",
                     total_snippets=len(code_snippets),
                     error=str(e))
            return [[0.0] * 768] * len(code_snippets)

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        start_time = time.time()
        try:
            tensor1 = torch.tensor(embedding1).unsqueeze(0)
            tensor2 = torch.tensor(embedding2).unsqueeze(0)
            
            cos = torch.nn.CosineSimilarity(dim=1)
            similarity = cos(tensor1, tensor2).item()
            
            duration = (time.time() - start_time) * 1000
            self._log("debug", "Computed similarity successfully",
                     similarity=similarity,
                     duration_ms=duration)
                     
            return similarity
            
        except Exception as e:
            self._log("error", "Failed to compute similarity",
                     error=str(e))
            return 0.0 