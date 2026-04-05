"""
Eddie Assistant Service
Backend chat orchestration for the dashboard Eddie assistant.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.ai.llm import get_llm_service


class EddieAssistantService:
    """Service wrapper for Eddie assistant chat."""

    def __init__(self):
        self.llm = get_llm_service()

    def chat(self, messages: List[Dict[str, str]], page_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Run Eddie chat using Groq-backed LLM service.

        Args:
            messages: list of chat messages with role/content
            page_context: optional context like current dashboard page

        Returns:
            Dict with success/response metadata
        """
        try:
            response = self.llm.eddie_chat(messages=messages, page_context=page_context)
            return {
                "success": True,
                "type": "eddie_chat",
                "response": response,
            }
        except Exception as e:
            return {
                "success": False,
                "type": "eddie_chat",
                "error": str(e),
            }
