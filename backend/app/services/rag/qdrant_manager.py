"""Qdrant vector database manager."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Any, Optional
from . import config

class QdrantManager:
    """Manages Qdrant vector database operations."""
    
    def __init__(self):
        """Initialize Qdrant client."""
        # Check if using cloud (has API key)
        if config.QDRANT_API_KEY:
            self.client = QdrantClient(
                url=f"https://{config.QDRANT_HOST}:{config.QDRANT_PORT}",
                api_key=config.QDRANT_API_KEY
            )
        else:
            # Local Qdrant
            self.client = QdrantClient(
                host=config.QDRANT_HOST,
                port=config.QDRANT_PORT
            )
        self.collection_name = config.QDRANT_COLLECTION_NAME
    
    def test_connection(self) -> bool:
        """Test connection to Qdrant server."""
        try:
            collections = self.client.get_collections()
            print(f"✓ Connected to Qdrant at {config.QDRANT_HOST}:{config.QDRANT_PORT}")
            print(f"  Existing collections: {len(collections.collections)}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to Qdrant: {e}")
            return False
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        transaction_type: Optional[str] = None,
        doc_type: Optional[str] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents.
        
        Args:
            query_vector: Embedding vector of the query
            limit: Maximum number of results to return
            transaction_type: Filter by transaction type (834, 835, 837I, 837P)
            doc_type: Filter by document type (tr3, claims_manual, code_list)
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of search results with payload and score
        """
        try:
            # Build filter
            filter_conditions = []
            if transaction_type:
                filter_conditions.append(
                    FieldCondition(
                        key="transaction_type",
                        match=MatchValue(value=transaction_type)
                    )
                )
            if doc_type:
                filter_conditions.append(
                    FieldCondition(
                        key="doc_type",
                        match=MatchValue(value=doc_type)
                    )
                )
            
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=search_filter,
                score_threshold=score_threshold
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "source_doc": result.payload.get("source_doc", ""),
                    "page": result.payload.get("page"),
                    "doc_type": result.payload.get("doc_type", ""),
                    "transaction_type": result.payload.get("transaction_type"),
                    "metadata": result.payload
                })
            
            return formatted_results
        
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            points_count = getattr(info, "points_count", None)
            vectors_count = getattr(info, "vectors_count", None)
            if vectors_count is None:
                vectors_count = points_count

            distance = None
            try:
                config = getattr(info, "config", None)
                params = getattr(config, "params", None) if config else None
                vectors = getattr(params, "vectors", None) if params else None
                if hasattr(vectors, "distance"):
                    distance = vectors.distance
                elif isinstance(vectors, dict) and vectors:
                    first = next(iter(vectors.values()), None)
                    distance = getattr(first, "distance", None)
            except Exception:
                distance = None

            return {
                "name": self.collection_name,
                "vectors_count": vectors_count,
                "points_count": points_count,
                "status": getattr(info, "status", None),
                "config": {
                    "distance": distance
                }
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {}
