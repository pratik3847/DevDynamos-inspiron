"""
Validator Agent
Represents the validation phase. Takes the parsed JSON from state, calls `services.validation.validator`,
and appends any validation errors/warnings back into the session document.

Enhanced with RAG Knowledge System:
- Queries TR3 implementation guides for validation rules
- Provides regulatory context for errors
- References specific documentation pages
"""
from typing import Dict, Any, Optional
from ..validation import EDIValidator, ValidationConfig, ValidationResult
from ..rag import RAGClient


class ValidatorAgent:
    """
    AI-powered validation orchestrator
    Uses core validator and adds intelligent explanations
    """
    
    def __init__(self, llm_service=None, config: Optional[ValidationConfig] = None):
        """
        Initialize validator agent
        
        Args:
            llm_service: LLM service for generating explanations (optional)
            config: Validation configuration
        """
        self.llm = llm_service
        self.validator = EDIValidator(config or ValidationConfig())
        self.rag = RAGClient()  # RAG knowledge system for TR3 guidance
    
    async def execute(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute validation workflow
        
        Args:
            session_state: Current session state with parsed EDI data
        
        Returns:
            Updated session state with validation results
        """
        # Extract parsed EDI data from session
        parsed_data = session_state.get("parsed_edi")
        transaction_type = session_state.get("transaction_type", "837P")
        
        if not parsed_data:
            return self._handle_missing_data(session_state)
        
        # Run core validation
        validation_result = self.validator.validate(
            edi_data=parsed_data,
            transaction_type=transaction_type
        )
        
        # Enhance with AI explanations if LLM available
        if self.llm and validation_result.errors:
            validation_result = await self._enhance_with_ai(validation_result)
        
        # Update session state
        session_state.update({
            "validation_result": validation_result.to_dict(),
            "validation_status": validation_result.status,
            "total_errors": validation_result.total_errors,
            "total_warnings": validation_result.total_warnings,
            "fixable_errors": validation_result.fixable_errors
        })
        
        return session_state
    
    def validate_sync(
        self, 
        edi_data: Dict[str, Any], 
        transaction_type: str = "837P"
    ) -> ValidationResult:
        """
        Synchronous validation (no AI enhancement)
        
        Args:
            edi_data: Parsed EDI data
            transaction_type: Transaction type
        
        Returns:
            ValidationResult
        """
        return self.validator.validate(edi_data, transaction_type)
    
    def validate_quick(
        self, 
        edi_data: Dict[str, Any], 
        transaction_type: str = "837P"
    ) -> ValidationResult:
        """
        Quick validation (skip external APIs)
        
        Args:
            edi_data: Parsed EDI data
            transaction_type: Transaction type
        
        Returns:
            ValidationResult
        """
        return self.validator.validate_quick(edi_data, transaction_type)
    
    async def _enhance_with_ai(self, result: ValidationResult) -> ValidationResult:
        """
        Use RAG and LLM to generate human-readable explanations and suggestions
        
        Args:
            result: Validation result to enhance
        
        Returns:
            Enhanced validation result with RAG-powered context
        """
        # Query RAG for relevant TR3 documentation
        for error in result.errors:
            try:
                # Extract transaction type and segment from error
                transaction_type = getattr(result, 'transaction_type', '837P')
                segment_id = error.get('segment', '')
                
                # Query RAG for validation rules
                rag_results = self.rag.query(
                    f"What are the validation rules for {segment_id} in {transaction_type}?",
                    transaction_type=transaction_type,
                    doc_type="tr3",
                    top_k=2
                )
                
                # Enhance error with RAG context
                if rag_results:
                    error['rag_context'] = {
                        'documentation': rag_results[0]['text'][:300],
                        'source': rag_results[0]['source_doc'],
                        'page': rag_results[0]['page'],
                        'relevance': rag_results[0]['score']
                    }
                    
                    # Add regulatory explanation
                    if 'explanation' not in error or not error['explanation']:
                        error['explanation'] = f"According to {rag_results[0]['source_doc']}: {rag_results[0]['text'][:200]}"
                
            except Exception as e:
                # Gracefully handle RAG query failures
                error['rag_error'] = str(e)
        
        # TODO: Implement LLM-based enhancement if available
        # This would use the LLM to:
        # - Generate more detailed explanations
        # - Provide context-aware suggestions
        # - Identify patterns in errors
        # - Suggest root cause fixes
        
        return result
    
    def _handle_missing_data(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle case where parsed data is missing"""
        session_state.update({
            "validation_result": {
                "status": "FAILED",
                "errors": [{
                    "layer": "SYSTEM",
                    "type": "SEGMENT",
                    "severity": "CRITICAL",
                    "segment": "SYSTEM",
                    "error": "No parsed EDI data available for validation",
                    "suggestion": "Ensure EDI file is parsed before validation"
                }],
                "warnings": []
            },
            "validation_status": "FAILED"
        })
        return session_state

