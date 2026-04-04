"""
Parser Agent
Represents the parsing phase of the pipeline. Its job is to take the raw EDI string,
call `services.parser.parser`, and update the session state with the structured JSON.
"""

from typing import Any, Dict, Optional

from app.services.parser.parser import parser_agent as parse_edi


class ParserAgent:
	"""Thin wrapper around the core parser service."""

	def parse_sync(self, edi_text: str) -> Dict[str, Any]:
		return parse_edi(edi_text)

	async def execute(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
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

		parsed = self.parse_sync(raw)
		session_state.update(
			{
				"parsed_edi": parsed,
				"parsing_status": parsed.get("status", "parsed"),
			}
		)
		return session_state
