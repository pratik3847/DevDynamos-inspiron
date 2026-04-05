"""
AI Explainer Routes
Endpoints for interacting with the AI explainer agent (chat, questions about the EDI).
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.services.agents.explainer_agent import ExplainerAgent
from app.services.ai.eddie_service import EddieAssistantService

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])

# Lazy initialization of explainer agent
_explainer = None
_eddie = None

def get_explainer() -> ExplainerAgent:
    """Get or create the explainer agent (lazy initialization)."""
    global _explainer
    if _explainer is None:
        _explainer = ExplainerAgent()
    return _explainer


def get_eddie() -> EddieAssistantService:
    """Get or create Eddie assistant service (lazy initialization)."""
    global _eddie
    if _eddie is None:
        _eddie = EddieAssistantService()
    return _eddie


# =============== Pydantic Models ===============

class QuestionRequest(BaseModel):
    """Model for EDI question"""
    question: str
    edi_context: Optional[str] = None


class SegmentExplanationRequest(BaseModel):
    """Model for segment explanation request"""
    segment_id: str
    segment_content: Optional[str] = None


class ErrorAnalysisRequest(BaseModel):
    """Model for error analysis request"""
    error_message: str
    edi_content: Optional[str] = None


class FixSuggestionRequest(BaseModel):
    """Model for fix suggestion request"""
    issue_description: str
    edi_content: Optional[str] = None


class ChatMessage(BaseModel):
    """Model for chat message"""
    role: str  # "user" or "assistant"
    content: str


class MultiTurnChatRequest(BaseModel):
    """Model for multi-turn chat"""
    messages: List[ChatMessage]


class EddieChatRequest(BaseModel):
    """Model for Eddie chat request"""
    messages: List[ChatMessage]
    page_context: Optional[str] = None


# =============== API Endpoints ===============

@router.post("/ask-question")
async def ask_question(request: QuestionRequest):
    """
    Ask the AI assistant a question about EDI files, segments, or structure.
    
    Args:
        request: QuestionRequest with question and optional edi_context
    
    Returns:
        Response with AI answer
    """
    try:
        explainer = get_explainer()
        result = explainer.answer_edi_question(
            question=request.question,
            edi_context=request.edi_context
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to process question"))
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain-segment")
async def explain_segment(request: SegmentExplanationRequest):
    """
    Get an explanation of an EDI segment.
    
    Args:
        request: SegmentExplanationRequest with segment_id and optional content
    
    Returns:
        Response with segment explanation
    """
    try:
        explainer = get_explainer()
        result = explainer.explain_segment(
            segment_id=request.segment_id,
            segment_content=request.segment_content
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to explain segment"))
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-error")
async def analyze_error(request: ErrorAnalysisRequest):
    """
    Analyze an EDI error and get fixes.
    
    Args:
        request: ErrorAnalysisRequest with error message and optional EDI content
    
    Returns:
        Response with error analysis and fixes
    """
    try:
        explainer = get_explainer()
        result = explainer.analyze_error(
            error_message=request.error_message,
            edi_content=request.edi_content
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to analyze error"))
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-fixes")
async def suggest_fixes(request: FixSuggestionRequest):
    """
    Get fix suggestions for an EDI issue.
    
    Args:
        request: FixSuggestionRequest with issue description and optional EDI content
    
    Returns:
        Response with fix suggestions
    """
    try:
        explainer = get_explainer()
        result = explainer.suggest_fixes(
            issue_description=request.issue_description,
            edi_content=request.edi_content
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to suggest fixes"))
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(request: MultiTurnChatRequest):
    """
    Multi-turn conversation about EDI.
    
    Args:
        request: MultiTurnChatRequest with list of messages
    
    Returns:
        Response with AI's next message
    """
    try:
        explainer = get_explainer()
        # Convert ChatMessage objects to dicts for LLM
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        result = explainer.multi_turn_chat(messages)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to process chat"))
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eddie-chat")
async def eddie_chat(request: EddieChatRequest):
    """
    Multi-turn Eddie assistant conversation for dashboard users.

    Args:
        request: EddieChatRequest with list of messages and optional page context

    Returns:
        Response with Eddie assistant message
    """
    try:
        eddie = get_eddie()
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        result = eddie.chat(messages=messages, page_context=request.page_context)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to process Eddie chat"))

        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for AI service."""
    return {
        "status": "healthy",
        "service": "AI Assistant",
        "endpoints": [
            "/api/ai/ask-question",
            "/api/ai/explain-segment",
            "/api/ai/analyze-error",
            "/api/ai/suggest-fixes",
            "/api/ai/chat",
            "/api/ai/eddie-chat",
            "/api/ai/health"
        ]
    }
