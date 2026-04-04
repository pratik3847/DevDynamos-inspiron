"""
Explainer Agent
Handles user questions about the EDI file, segments, errors, and fixes by calling the LLM service.
"""
from typing import Optional, Dict, Any
from app.services.ai.llm import get_llm_service

class ExplainerAgent:
    """Agent for explaining EDI concepts, errors, and providing fixes."""
    
    def __init__(self):
        """Initialize the explainer agent with LLM service."""
        self.llm = get_llm_service()
    
    def answer_edi_question(self, question: str, edi_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Answer user questions about EDI files, segments, structure.
        
        Args:
            question: User's question
            edi_context: Optional EDI content for context
        
        Returns:
            Dict with 'answer', 'type', 'success', and optional 'error'
        """
        try:
            answer = self.llm.ask_about_edi(question, context=edi_context)
            return {
                "success": True,
                "type": "question_answer",
                "answer": answer,
                "question": question
            }
        except Exception as e:
            return {
                "success": False,
                "type": "question_answer",
                "error": str(e),
                "question": question
            }
    
    def explain_segment(self, segment_id: str, segment_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Explain an EDI segment.
        
        Args:
            segment_id: EDI segment ID (e.g., 'ISA', 'GS', 'ST', 'CLP')
            segment_content: Optional segment content for detailed explanation
        
        Returns:
            Dict with segment explanation and metadata
        """
        try:
            explanation = self.llm.explain_edi_segment(segment_id, segment_content)
            return {
                "success": True,
                "type": "segment_explanation",
                "segment_id": segment_id,
                "explanation": explanation
            }
        except Exception as e:
            return {
                "success": False,
                "type": "segment_explanation",
                "segment_id": segment_id,
                "error": str(e)
            }
    
    def analyze_error(self, error_message: str, edi_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze an EDI error and provide fixes.
        
        Args:
            error_message: The error message or description
            edi_content: Optional EDI content related to the error
        
        Returns:
            Dict with error analysis and suggested fixes
        """
        try:
            analysis = self.llm.analyze_edi_error(error_message, edi_content)
            return {
                "success": True,
                "type": "error_analysis",
                "error_message": error_message,
                "analysis": analysis
            }
        except Exception as e:
            return {
                "success": False,
                "type": "error_analysis",
                "error_message": error_message,
                "error": str(e)
            }
    
    def suggest_fixes(self, issue_description: str, edi_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Suggest fixes for EDI issues.
        
        Args:
            issue_description: Description of the issue
            edi_content: Optional EDI content to analyze
        
        Returns:
            Dict with suggested fixes
        """
        try:
            fixes = self.llm.suggest_fixes(issue_description, edi_content)
            return {
                "success": True,
                "type": "fix_suggestions",
                "issue": issue_description,
                "suggestions": fixes
            }
        except Exception as e:
            return {
                "success": False,
                "type": "fix_suggestions",
                "issue": issue_description,
                "error": str(e)
            }
    
    def multi_turn_chat(self, messages: list) -> Dict[str, Any]:
        """
        Handle multi-turn conversations about EDI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            Dict with assistant response
        """
        try:
            response = self.llm.multi_turn_conversation(messages)
            return {
                "success": True,
                "type": "chat",
                "response": response,
                "message_count": len(messages)
            }
        except Exception as e:
            return {
                "success": False,
                "type": "chat",
                "error": str(e)
            }
