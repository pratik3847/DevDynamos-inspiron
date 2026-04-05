"""RAG Client - Main interface for querying the knowledge base."""
from typing import List, Dict, Any, Optional
from .qdrant_manager import QdrantManager
from .embedding_model import EmbeddingModel
from . import config

class RAGClient:
    """Main client for interacting with the RAG knowledge base.
    
    This provides a simple interface for other agents to query the
    HIPAA EDI documentation knowledge base.
    
    Example usage:
        >>> rag = RAGClient()
        >>> results = rag.query("What segments are required in Loop 2310B for 837P?")
        >>> for result in results:
        ...     print(f"Source: {result['source_doc']} (page {result['page']})")
        ...     print(f"Content: {result['text']}")
        ...     print(f"Relevance: {result['score']:.2%}")
    """
    
    def __init__(self):
        """Initialize the RAG client."""
        self.qdrant = QdrantManager()
        self.embedder = EmbeddingModel()
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Qdrant on initialization."""
        try:
            info = self.qdrant.get_collection_info()
            if info:
                print(f"✓ RAG Client ready - {info.get('vectors_count', 0):,} embeddings available")
        except Exception as e:
            print(f"⚠ RAG Client initialized but collection not accessible: {e}")
    
    def query(
        self,
        question: str,
        top_k: int = None,
        transaction_type: Optional[str] = None,
        doc_type: Optional[str] = None,
        min_score: float = None
    ) -> List[Dict[str, Any]]:
        """Query the knowledge base with a natural language question.
        
        Args:
            question: Natural language question about EDI/HIPAA
            top_k: Number of results to return (default: 5, max: 20)
            transaction_type: Filter by transaction type (834, 835, 837I, 837P)
            doc_type: Filter by document type (tr3, claims_manual, code_list)
            min_score: Minimum similarity score (0.0-1.0, default: 0.7)
            
        Returns:
            List of relevant document chunks with metadata and scores
            
        Example:
            >>> rag = RAGClient()
            >>> results = rag.query(
            ...     "What is Loop 2310B in 837P?",
            ...     top_k=3,
            ...     transaction_type="837P"
            ... )
        """
        # Validate parameters
        if not question or not question.strip():
            return []
        
        top_k = min(top_k or config.DEFAULT_TOP_K, config.MAX_TOP_K)
        min_score = min_score or config.SIMILARITY_THRESHOLD
        
        # Generate query embedding
        query_vector = self.embedder.encode(question)
        
        # Search
        results = self.qdrant.search(
            query_vector=query_vector,
            limit=top_k,
            transaction_type=transaction_type,
            doc_type=doc_type,
            score_threshold=min_score
        )
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base.
        
        Returns:
            Dictionary with collection statistics
        """
        return self.qdrant.get_collection_info()
    
    def search_by_transaction(self, question: str, transaction_type: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Convenience method to search within a specific transaction type.
        
        Args:
            question: Natural language question
            transaction_type: Transaction type (834, 835, 837I, 837P)
            top_k: Number of results
            
        Returns:
            List of relevant results filtered by transaction type
        """
        return self.query(question, top_k=top_k, transaction_type=transaction_type)
    
    def search_tr3_guides(self, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search only in TR3 implementation guides.
        
        Args:
            question: Natural language question
            top_k: Number of results
            
        Returns:
            List of relevant results from TR3 guides
        """
        return self.query(question, top_k=top_k, doc_type="tr3")
    
    def search_claims_manual(self, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search only in CMS Claims Processing Manual.
        
        Args:
            question: Natural language question
            top_k: Number of results
            
        Returns:
            List of relevant results from CMS manual
        """
        return self.query(question, top_k=top_k, doc_type="claims_manual")
    
    def search_code_lists(self, code: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for medical codes (ICD-10, CARC, RARC, POS).
        
        Args:
            code: Code to search for (e.g., "A00.0", "CO-1", "POS-11")
            top_k: Number of results
            
        Returns:
            List of matching codes with descriptions
        """
        return self.query(code, top_k=top_k, doc_type="code_list")
