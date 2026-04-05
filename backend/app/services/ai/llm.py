"""
LLM Core Service
Wrappers and utility functions for Groq API calls. Keeps prompt logic abstracted.

Key behaviors:
- Uses `GROQ_API_KEY` and `GROQ_MODEL` from environment (see `app.config`).
- If `GROQ_MODEL=auto` (or empty), selects an available model via the Groq SDK model listing.
- If a request fails due to a decommissioned/invalid model, refreshes the model list and retries once.
"""

from __future__ import annotations

from typing import Optional, List, Dict

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL


class LLMService:
    """Service for handling LLM interactions via Groq API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Only fall back to env defaults if caller passed None.
        self.api_key = GROQ_API_KEY if api_key is None else api_key
        self.model = GROQ_MODEL if model is None else model

        self.client: Optional[Groq] = None
        self._available_models: Optional[List[str]] = None
        self._auto_model = (not self.model) or str(self.model).strip().lower() == "auto"

        if self.api_key:
            self.client = Groq(api_key=self.api_key)

    def _ensure_client(self) -> bool:
        """Ensure API key and client are initialized."""
        if not self.api_key:
            return False
        if self.client is None:
            self.client = Groq(api_key=self.api_key)

        if self._auto_model:
            picked = self._pick_available_model(refresh=False)
            if picked:
                self.model = picked

        return True

    def _get_available_model_ids(self, *, refresh: bool) -> List[str]:
        if self._available_models is not None and not refresh:
            return list(self._available_models)

        if self.client is None:
            self._available_models = []
            return []

        try:
            models_obj = getattr(self.client, "models", None)
            if models_obj is None:
                self._available_models = []
                return []

            listing = models_obj.list()
            data = getattr(listing, "data", None)
            if data is None and isinstance(listing, dict):
                data = listing.get("data")

            ids: List[str] = []
            for item in data or []:
                mid = getattr(item, "id", None)
                if mid is None and isinstance(item, dict):
                    mid = item.get("id")
                if mid:
                    ids.append(str(mid))

            self._available_models = ids
            return list(ids)
        except Exception:
            self._available_models = []
            return []

    def _pick_available_model(self, *, refresh: bool) -> str:
        """Pick a reasonable default model from what Groq reports as available."""
        ids = self._get_available_model_ids(refresh=refresh)
        if not ids:
            return ""

        # Simple preference ordering by substring; keep it conservative.
        preference = [
            "llama-3.1",
            "llama3",
            "llama-3",
            "llama",
            "mixtral",
            "gemma",
        ]

        lowered = [(mid, mid.lower()) for mid in ids]
        for token in preference:
            for mid, low in lowered:
                if token in low:
                    return mid

        return ids[0]

    @staticmethod
    def _looks_like_decommissioned_or_invalid_model(err: Exception) -> bool:
        msg = str(err).lower()
        return (
            "decommissioned" in msg
            or "model_decommissioned" in msg
            or "invalid model" in msg
            or "model_not_found" in msg
            or "not found" in msg
        )

    @staticmethod
    def _format_groq_error(prefix: str, err: Exception) -> str:
        msg = str(err)
        lower = msg.lower()

        if "decommissioned" in lower or "model_decommissioned" in lower:
            return (
                f"{prefix}: Groq model is decommissioned. "
                "Set `GROQ_MODEL=auto` (recommended) or a supported Groq model id, then restart the backend. "
                f"Details: {msg}"
            )

        return f"{prefix}: {msg}"

    @staticmethod
    def _not_configured_message(feature: str) -> str:
        return (
            f"AI is not configured for {feature}. "
            "Set `GROQ_API_KEY` in your environment (or backend/.env) and restart the backend."
        )

    def _chat_completion(self, messages: List[Dict[str, str]], *, max_tokens: int, temperature: float) -> str:
        if self.client is None:
            raise RuntimeError("Groq client is not initialized")
        if not self.model:
            raise RuntimeError("No Groq model is configured")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content

    def _chat_with_retry(self, messages: List[Dict[str, str]], *, max_tokens: int, temperature: float) -> str:
        """Make one Groq call with a single refresh+retry on model issues."""
        try:
            return self._chat_completion(messages, max_tokens=max_tokens, temperature=temperature)
        except Exception as e:
            if not self._looks_like_decommissioned_or_invalid_model(e):
                raise

            # If auto is enabled, refresh the model list and try once more.
            if self._auto_model:
                picked = self._pick_available_model(refresh=True)
                if picked:
                    self.model = picked

            return self._chat_completion(messages, max_tokens=max_tokens, temperature=temperature)

    def ask_about_edi(self, question: str, context: Optional[str] = None) -> str:
        if not self._ensure_client():
            return self._not_configured_message("ask-question")

        system_prompt = self._get_edi_system_prompt()
        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        if context:
            messages.append({
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            })
        else:
            messages.append({"role": "user", "content": question})

        try:
            return self._chat_with_retry(messages, max_tokens=1024, temperature=0.7)
        except Exception as e:
            return self._format_groq_error("Error calling Groq API", e)

    def analyze_edi_error(self, error_message: str, edi_content: Optional[str] = None) -> str:
        if not self._ensure_client():
            return self._not_configured_message("analyze-error")

        system_prompt = self._get_edi_system_prompt()
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self._format_error_analysis_prompt(error_message, edi_content)},
        ]

        try:
            return self._chat_with_retry(messages, max_tokens=1500, temperature=0.7)
        except Exception as e:
            return self._format_groq_error("Error analyzing EDI error", e)

    def explain_edi_segment(
        self,
        segment_id: str,
        segment_content: Optional[str] = None,
        context: Optional[str] = None,
    ) -> str:
        if not self._ensure_client():
            return self._not_configured_message("explain-segment")

        system_prompt = self._get_edi_system_prompt()

        style = (
            "Write a clean, concise explanation in 2–3 short sentences. "
            "Plain English only: no headings, no bullet points, no markdown, no disclaimers. "
            "Ground your explanation in the actual segment content: use qualifiers/codes in the segment (e.g., NM101) to identify what entity it represents. "
            "For NM1 segments, use these common NM101 meanings: 82=Rendering Provider, 85=Billing Provider, IL=Subscriber, QC=Patient, PR=Payer, 40=Receiver, 41=Submitter. "
            "If the segment content is insufficient to determine the exact role, say that explicitly instead of guessing. "
            "Do not restate the full segment string; only refer to the few most important fields. "
            "If you mention element positions, keep it to at most two (e.g., NM101, NM108)."
        )

        if segment_content and context:
            question = (
                f"{style}\n\n"
                f"Context (TR3 / docs):\n{context}\n\n"
                f"Explain what the X12 segment '{segment_id}' means and what this specific instance is doing. "
                "Focus on what it represents in the transaction and why it matters.\n\n"
                f"Segment instance: {segment_content}"
            )
        elif segment_content:
            question = (
                f"{style}\n\n"
                f"Explain what the X12 segment '{segment_id}' means and what this specific instance is doing. "
                "Focus on what it represents in the transaction and why it matters.\n\n"
                f"Segment instance: {segment_content}"
            )
        elif context:
            question = (
                f"{style}\n\n"
                f"Context (TR3 / docs):\n{context}\n\n"
                f"Explain what the X12 segment '{segment_id}' is used for and why it matters."
            )
        else:
            question = (
                f"{style}\n\n"
                f"Explain what the X12 segment '{segment_id}' is used for and why it matters."
            )

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        try:
            return self._chat_with_retry(messages, max_tokens=160, temperature=0.2)
        except Exception as e:
            return self._format_groq_error("Error explaining EDI segment", e)

    def suggest_fixes(self, issue_description: str, edi_content: Optional[str] = None) -> str:
        if not self._ensure_client():
            return self._not_configured_message("suggest-fixes")

        system_prompt = self._get_edi_system_prompt()

        if edi_content:
            prompt = (
                f"I have an EDI issue: {issue_description}\n\nEDI Content:\n{edi_content}\n\n"
                "Please suggest specific fixes."
            )
        else:
            prompt = f"I have an EDI issue: {issue_description}\n\nPlease suggest fixes and solutions."

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            return self._chat_with_retry(messages, max_tokens=1500, temperature=0.7)
        except Exception as e:
            return self._format_groq_error("Error suggesting fixes", e)

    def multi_turn_conversation(self, messages: List[Dict[str, str]]) -> str:
        if not self._ensure_client():
            return self._not_configured_message("chat")

        system_prompt = self._get_edi_system_prompt()
        all_messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}] + list(messages)

        try:
            return self._chat_with_retry(all_messages, max_tokens=1024, temperature=0.7)
        except Exception as e:
            return self._format_groq_error("Error in conversation", e)

    def eddie_chat(self, messages: List[Dict[str, str]], page_context: Optional[str] = None) -> str:
        """Multi-turn Eddie assistant chat for dashboard workflows and API guidance."""
        if not self._ensure_client():
            return self._not_configured_message("eddie-chat")

        system_prompt = self._get_eddie_system_prompt(page_context=page_context)
        all_messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}] + list(messages)

        try:
            return self._chat_with_retry(all_messages, max_tokens=900, temperature=0.4)
        except Exception as e:
            return self._format_groq_error("Error in Eddie chat", e)

    @staticmethod
    def _get_edi_system_prompt() -> str:
        """Get the system prompt for EDI-specific assistance."""
        return """You are an expert EDI (Electronic Data Interchange) assistant specializing in healthcare billing and claims processing.

You have deep knowledge about:
- EDI file formats and standards (X12, HL7)
- EDI segments (ISA, GS, ST, SVD, CLP, NM1, etc.)
- Healthcare billing terminology (CARC codes, RARC codes, NPI, place of service)
- Common EDI errors and validation rules
- Best practices for EDI file creation and validation

Your responsibilities:
1. Answer user questions about EDI files, segments, and structure
2. Explain error messages and their causes
3. Provide specific, actionable fixes for EDI issues
4. Help users understand healthcare billing processes
5. Provide examples when helpful
6. Be clear, concise, and accurate

When users ask about errors or issues, always:
- Identify the root cause
- Explain why it matters
- Suggest specific corrections
- Provide examples when possible

Always maintain a professional, helpful tone and focus on practical solutions."""

    @staticmethod
    def _get_eddie_system_prompt(page_context: Optional[str] = None) -> str:
        """System prompt for Eddie dashboard assistant."""
        context_hint = f"Current page context: {page_context}." if page_context else ""
        return (
            "You are Eddie, the in-product AI assistant for an EDI dashboard platform. "
            "You help users with parser, validation, fixing workflow, upload flow, and backend API usage. "
            "Give concise, actionable answers in plain English. "
            "If a user asks about API behavior, explain likely endpoints and payload patterns clearly. "
            "Never invent that an operation succeeded unless the user explicitly confirms it. "
            "When uncertain, ask one clarifying question. "
            f"{context_hint}"
        )

    @staticmethod
    def _format_error_analysis_prompt(error_message: str, edi_content: Optional[str] = None) -> str:
        """Format the error analysis prompt."""
        if edi_content:
            return f"""Please analyze this EDI error and provide a solution:

Error: {error_message}

EDI Content:
{edi_content}

Please provide:
1. Root cause of the error
2. Why this is a problem
3. Step-by-step fix instructions
4. Prevention tips for the future"""

        return f"""Please analyze this EDI error and provide a solution:

Error: {error_message}

Please provide:
1. What this error means
2. Common causes
3. How to fix it
4. Prevention tips"""


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create a singleton LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
