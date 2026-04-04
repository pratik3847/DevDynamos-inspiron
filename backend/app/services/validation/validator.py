"""
Validator Core Service
Contains the logic to execute business rules against the parsed EDI JSON structure.
Main orchestrator for three-layer validation system.
"""
import time
from typing import Dict, Any, List, Optional
from .models import (
    ValidationResult,
    ValidationContext,
    ValidationError,
    ErrorSeverity,
    ErrorLayer,
    ErrorType,
)
from .engine import StructuralValidator, BusinessValidator, ExternalValidator


class ValidationConfig:
    """Configuration for validation engine"""
    
    def __init__(
        self,
        enable_external_validation: bool = True,
        max_errors_per_file: int = 1000,
        strict_mode: bool = False,
        collect_all_errors: bool = True
    ):
        self.enable_external_validation = enable_external_validation
        self.max_errors_per_file = max_errors_per_file
        self.strict_mode = strict_mode  # Fail on warnings
        self.collect_all_errors = collect_all_errors  # Don't stop on first error


class EDIValidator:
    """
    Main EDI Validation Engine
    Orchestrates three-layer validation: Structural -> Business -> External
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self.structural_validator = StructuralValidator()
        self.business_validator = BusinessValidator()
        self.external_validator = ExternalValidator(
            enable_external=self.config.enable_external_validation
        )
    
    def validate(
        self, 
        edi_data: Dict[str, Any], 
        transaction_type: str
    ) -> ValidationResult:
        """
        Execute complete validation pipeline
        
        Args:
            edi_data: Parsed EDI data structure
            transaction_type: Transaction type (837P, 835, 834)
        
        Returns:
            ValidationResult with all errors and warnings
        """
        start_time = time.time()
        
        # Initialize validation context
        context = self._create_context(edi_data, transaction_type)
        
        all_errors: List[ValidationError] = []
        all_warnings: List[ValidationError] = []
        
        # Layer 1: Structural Validation (always run)
        structural_errors = self._run_layer(
            "Structural",
            lambda: self.structural_validator.validate(context)
        )
        self._attach_error_metadata(structural_errors, context)
        all_errors.extend(structural_errors)
        
        # Check if we should continue (only stop if completely unparseable)
        if self._is_critical_failure(structural_errors):
            return self._create_result(
                context,
                all_errors,
                all_warnings,
                "FAILED",
                time.time() - start_time
            )
        
        # Layer 2: Business Validation (always run, even if Layer 1 failed)
        business_errors = self._run_layer(
            "Business",
            lambda: self.business_validator.validate(context)
        )
        self._attach_error_metadata(business_errors, context)
        all_errors.extend(business_errors)
        
        # Check max errors limit
        if len(all_errors) >= self.config.max_errors_per_file:
            all_warnings.append(
                ValidationError(
                    layer=ErrorLayer.BUSINESS,
                    type=ErrorType.SEGMENT,
                    severity=ErrorSeverity.WARNING,
                    segment="SYSTEM",
                    error=f"Maximum error limit reached ({self.config.max_errors_per_file})",
                    suggestion="Fix critical errors and re-validate"
                )
            )
            return self._create_result(
                context,
                all_errors[:self.config.max_errors_per_file],
                all_warnings,
                "FAILED",
                time.time() - start_time
            )
        
        # Layer 3: External Validation (async, non-blocking, warnings only)
        if self.config.enable_external_validation:
            external_warnings = self._run_layer(
                "External",
                lambda: self.external_validator.validate_sync(context)
            )
            self._attach_error_metadata(external_warnings, context)
            all_warnings.extend(external_warnings)
        
        # Determine final status
        status = self._determine_status(all_errors, all_warnings)
        
        processing_time = time.time() - start_time
        
        return self._create_result(
            context,
            all_errors,
            all_warnings,
            status,
            processing_time
        )
    
    def _create_context(
        self, 
        edi_data: Dict[str, Any], 
        transaction_type: str
    ) -> ValidationContext:
        """Create validation context from parser output"""
        # Normalize transaction types (some senders set ST01=837)
        if transaction_type == "837":
            transaction_type = "837P"

        context = ValidationContext(
            transaction_type=transaction_type,
            edi_data=edi_data
        )
        
        # Extract all segments from parser output (top-level + loops)
        all_segments = []
        
        # Add top-level segments
        if "segments" in edi_data:
            all_segments.extend(edi_data["segments"])
        
        # Extract segments from loops recursively
        if "loops" in edi_data:
            context.loops = edi_data["loops"]
            all_segments.extend(self._extract_segments_from_loops(edi_data["loops"]))
        
        context.segments = all_segments
        
        return context

    def _attach_error_metadata(self, errors: List[ValidationError], context: ValidationContext):
        """Enrich errors with consistent metadata needed by the API/UI."""
        for err in errors or []:
            # Populate rule_id/transaction_type for production-ready output schema
            if getattr(err, "rule_id", None) is None:
                setattr(err, "rule_id", getattr(err, "code", None))
            if getattr(err, "transaction_type", None) is None:
                setattr(err, "transaction_type", context.transaction_type)
            if getattr(err, "loop_id", None) is None:
                # Prefer explicit loop id; fall back to loop string if present
                setattr(err, "loop_id", getattr(err, "loop", None))
    
    def _extract_segments_from_loops(self, loops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recursively extract all segments from loop structure"""
        segments = []
        
        for loop in loops:
            # Add segments from this loop
            if "segments" in loop:
                segments.extend(loop["segments"])
            
            # Recursively process nested loops
            if "loops" in loop and loop["loops"]:
                segments.extend(self._extract_segments_from_loops(loop["loops"]))
        
        return segments
    
    def _run_layer(self, layer_name: str, validation_func) -> List[ValidationError]:
        """
        Run a validation layer with error handling
        Never stops execution - collects all errors
        """
        try:
            errors = validation_func()
            return errors if errors else []
        except Exception as e:
            # Layer failure should not stop validation
            layer_map = {
                "structural": ErrorLayer.STRUCTURAL,
                "business": ErrorLayer.BUSINESS,
                "external": ErrorLayer.EXTERNAL,
            }
            return [
                ValidationError(
                    layer=layer_map.get(layer_name.lower(), ErrorLayer.BUSINESS),
                    type=ErrorType.SEGMENT,
                    severity=ErrorSeverity.ERROR,
                    segment="SYSTEM",
                    error=f"{layer_name} validation layer failed: {str(e)}",
                    suggestion=f"Review {layer_name.lower()} validation logic"
                )
            ]
    
    def _is_critical_failure(self, errors: List[ValidationError]) -> bool:
        """Check if errors indicate file is completely unparseable"""
        critical_count = sum(
            1 for e in errors 
            if e.severity == ErrorSeverity.CRITICAL
        )
        
        # Only stop if multiple critical errors (file is corrupt)
        return critical_count >= 3
    
    def _determine_status(
        self, 
        errors: List[ValidationError], 
        warnings: List[ValidationError]
    ) -> str:
        """Determine final validation status"""
        if errors:
            return "FAILED"
        
        if warnings and self.config.strict_mode:
            return "FAILED"
        
        if warnings:
            return "PARTIAL"
        
        return "PASSED"
    
    def _create_result(
        self,
        context: ValidationContext,
        errors: List[ValidationError],
        warnings: List[ValidationError],
        status: str,
        processing_time: float
    ) -> ValidationResult:
        """Create final validation result"""
        return ValidationResult(
            status=status,
            transaction_type=context.transaction_type,
            errors=errors,
            warnings=warnings,
            context=context,
            processing_time=processing_time
        )
    
    def validate_quick(
        self, 
        edi_data: Dict[str, Any], 
        transaction_type: str
    ) -> ValidationResult:
        """
        Quick validation (Layer 1 + 2 only, skip external)
        Faster validation for real-time use cases
        """
        original_config = self.config.enable_external_validation
        self.config.enable_external_validation = False
        
        result = self.validate(edi_data, transaction_type)
        
        self.config.enable_external_validation = original_config
        return result


class ValidatorFactory:
    """Factory for creating validators with different configurations"""
    
    @staticmethod
    def create_standard_validator() -> EDIValidator:
        """Create validator with standard configuration"""
        return EDIValidator(ValidationConfig())
    
    @staticmethod
    def create_strict_validator() -> EDIValidator:
        """Create validator with strict mode (warnings = errors)"""
        config = ValidationConfig(strict_mode=True)
        return EDIValidator(config)
    
    @staticmethod
    def create_quick_validator() -> EDIValidator:
        """Create validator without external validation"""
        config = ValidationConfig(enable_external_validation=False)
        return EDIValidator(config)
    
    @staticmethod
    def create_custom_validator(
        enable_external: bool = True,
        max_errors: int = 1000,
        strict_mode: bool = False
    ) -> EDIValidator:
        """Create validator with custom configuration"""
        config = ValidationConfig(
            enable_external_validation=enable_external,
            max_errors_per_file=max_errors,
            strict_mode=strict_mode
        )
        return EDIValidator(config)
