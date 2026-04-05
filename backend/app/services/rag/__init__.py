"""RAG (Retrieval-Augmented Generation) Knowledge Service.

This service provides semantic search over HIPAA EDI documentation including:
- TR3 Implementation Guides (834, 835, 837I, 837P)
- CMS Claims Processing Manual
- ICD-10, CARC, RARC, POS code lists
- X12 segment dictionaries

Total embeddings: 240,054
Vector database: Qdrant Cloud
"""

try:
	from .rag_client import RAGClient
except Exception:
	class RAGClient:  # type: ignore[no-redef]
		"""Fallback no-op RAG client when optional vector/embedding deps are unavailable."""

		def __init__(self, *args, **kwargs):
			pass

		def query(self, *args, **kwargs):
			return []

__all__ = ["RAGClient"]
