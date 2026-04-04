"""
Validator Agent
Represents the validation phase. Takes the parsed JSON from state, calls `services.validation.validator`,
and appends any validation errors/warnings back into the session document.
"""
from typing import Dict, Any, Optional
from ..validation import EDIValidator, ValidationConfig, ValidationResult


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
        Use LLM to generate human-readable explanations and suggestions
        
        Args:
            result: Validation result to enhance
        
        Returns:
            Enhanced validation result
        """
        # TODO: Implement LLM-based enhancement
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

