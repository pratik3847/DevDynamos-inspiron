"""Embedding model for converting text to vectors."""
from sentence_transformers import SentenceTransformer
from typing import List, Union
from . import config

class EmbeddingModel:
    """Handles text-to-vector embedding generation."""

    _singleton = None
    _singleton_name = None

    def __new__(cls, model_name: str = None):
        name = model_name or config.EMBEDDING_MODEL_NAME
        if cls._singleton is None or cls._singleton_name != name:
            cls._singleton = super().__new__(cls)
            cls._singleton_name = name
            cls._singleton._initialized = False
        return cls._singleton

    def __init__(self, model_name: str = None):
        """Initialize the embedding model.

        Args:
            model_name: Name of the sentence-transformers model
        """
        if getattr(self, "_initialized", False):
            return
        self.model_name = model_name or config.EMBEDDING_MODEL_NAME
        print(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print(f"✓ Model loaded (dimension: {config.EMBEDDING_DIMENSION})")
        self._initialized = True
    
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
