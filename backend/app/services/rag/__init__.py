"""RAG (Retrieval-Augmented Generation) Knowledge Service.

This service provides semantic search over HIPAA EDI documentation including:
- TR3 Implementation Guides (834, 835, 837I, 837P)
- CMS Claims Processing Manual
- ICD-10, CARC, RARC, POS code lists
- X12 segment dictionaries

Total embeddings: 240,054
Vector database: Qdrant Cloud
"""

from .rag_client import RAGClient

__all__ = ["RAGClient"]
