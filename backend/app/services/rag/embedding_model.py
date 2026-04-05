"""Embedding model for converting text to vectors."""
from sentence_transformers import SentenceTransformer
from typing import List, Union
from . import config

class EmbeddingModel:
    """Handles text-to-vector embedding generation."""
    
    def __init__(self, model_name: str = None):
        """Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name or config.EMBEDDING_MODEL_NAME
        print(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print(f"✓ Model loaded (dimension: {config.EMBEDDING_DIMENSION})")
    
    def encode(self, text: Union[str, List[str]], show_progress: bool = False) -> Union[List[float], List[List[float]]]:
        """Convert text to embedding vector(s).
        
        Args:
            text: Single text string or list of text strings
            show_progress: Show progress bar for batch encoding
            
        Returns:
            Embedding vector(s) as list or list of lists
        """
        embeddings = self.model.encode(
            text,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        # Convert numpy array to list
        if isinstance(text, str):
            return embeddings.tolist()
        else:
            return [emb.tolist() for emb in embeddings]
    
    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return config.EMBEDDING_DIMENSION
