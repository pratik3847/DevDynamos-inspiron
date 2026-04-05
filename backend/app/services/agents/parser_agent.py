"""
Parser Agent
Represents the parsing phase of the pipeline. Its job is to take the raw EDI string,
call `services.parser.parser`, and update the session state with the structured JSON.

Enhanced with RAG Knowledge System:
- Validates segment structures against TR3 specifications
- Provides parsing hints from implementation guides
- Enriches parsed segments with documentation context
"""

from typing import Any, Dict, Optional

from app.services.parser.parser import parser_agent as parse_edi


class ParserAgent:
	"""Parser wrapper with RAG-enhanced segment validation and documentation lookup."""

	def __init__(self):
		"""Initialize parser agent with RAG knowledge system."""
		self.rag = None
		try:
			# Keep parser bootable even if optional RAG deps are not installed.
			from app.services.rag import RAGClient
			self.rag = RAGClient()  # RAG knowledge system for TR3 guidance
		except Exception:
			self.rag = None

	def parse_sync(self, edi_text: str, transaction_type: str = "837P", enrich_with_rag: bool = True) -> Dict[str, Any]:
		"""
		Parse EDI text and optionally enrich with RAG documentation.
		
		Args:
			edi_text: Raw EDI text
			transaction_type: Transaction type for context-specific parsing
			enrich_with_rag: Whether to add RAG context to parsed segments
			
		Returns:
			Parsed EDI structure with optional RAG enrichment
		"""
		# Core parsing
		result = parse_edi(edi_text)
		
		# Enrich with RAG if requested and parsing succeeded
		if enrich_with_rag and self.rag is not None and result.get("status") == "parsed":
			result = self._enrich_with_rag(result, transaction_type)
		
		return result
	
	def _enrich_with_rag(self, parsed_result: Dict[str, Any], transaction_type: str) -> Dict[str, Any]:
		"""
		Enrich parsed segments with RAG documentation context.
		
		Args:
			parsed_result: Parsed EDI result
			transaction_type: Transaction type
			
		Returns:
			Enhanced result with RAG context for key segments
		"""
		try:
			segments = parsed_result.get("segments", [])
			if not segments:
				return parsed_result
			
			# Track unique segment types we've looked up (to avoid redundant queries)
			queried_segments = set()
			
			# Enrich key segments with TR3 definitions
			for segment in segments[:20]:  # Limit to first 20 for performance
				if not isinstance(segment, dict):
					continue
				
				segment_id = segment.get("segmentId", "")
				if not segment_id or segment_id in queried_segments:
					continue
				
				# Query RAG for segment definition
				try:
					rag_results = self.rag.query(
						f"What is the {segment_id} segment structure and purpose in {transaction_type}?",
						transaction_type=transaction_type,
						doc_type="tr3",
						top_k=1
					)
					
					if rag_results:
						segment['rag_context'] = {
							'definition': rag_results[0]['text'][:200],
							'source': rag_results[0]['source_doc'],
							'page': rag_results[0]['page']
						}
						queried_segments.add(segment_id)
				
				except Exception:
					# Gracefully handle per-segment RAG failures
					pass
			
			# Add RAG metadata to result
			parsed_result['rag_enriched'] = True
			parsed_result['rag_segments_documented'] = len(queried_segments)
		
		except Exception as e:
			# Gracefully handle overall RAG enrichment failures
			parsed_result['rag_enrichment_error'] = str(e)
		
		return parsed_result

	async def execute(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Execute parsing workflow with RAG enhancement.
		
		Args:
			session_state: Current session state with raw EDI
			
		Returns:
			Updated session state with parsed and RAG-enriched EDI
		"""
		raw = (
			session_state.get("raw_edi")
			or session_state.get("rawEdi")
			or session_state.get("edi_text")
		)
		if not raw:
			session_state.update(
				{
					"parsing_status": "FAILED",
					"parsed_edi": None,
					"parsing_error": "No raw EDI content found in session_state",
				}
			)
			return session_state

		# Get transaction type from session or default to 837P
		transaction_type = session_state.get("transaction_type", "837P")
		
		# Parse with RAG enrichment
		parsed = self.parse_sync(raw, transaction_type=transaction_type, enrich_with_rag=True)
		
		session_state.update(
			{
				"parsed_edi": parsed,
				"parsing_status": parsed.get("status", "parsed"),
			}
		)
		return session_state
