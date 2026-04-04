"""
Validation Models
Data structures for validation results, errors, and context.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class ErrorSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ErrorLayer(str, Enum):
    STRUCTURAL = "STRUCTURAL"
    BUSINESS = "BUSINESS"
    EXTERNAL = "EXTERNAL"


class ErrorType(str, Enum):
    SEGMENT = "SEGMENT"
    FORMAT = "FORMAT"
    CODE = "CODE"
    CROSS_FIELD = "CROSS_FIELD"
    LOOP = "LOOP"
    SEQUENCE = "SEQUENCE"


@dataclass
class ValidationError:
    """Represents a single validation error"""
    layer: ErrorLayer
    type: ErrorType
    severity: ErrorSeverity
    segment: str

    # Production-friendly metadata
    rule_id: Optional[str] = None
    transaction_type: Optional[str] = None
    loop_id: Optional[str] = None

    field: Optional[str] = None
    error: str = ""
    suggestion: Optional[str] = None
    fixable: bool = False
    loop: Optional[str] = None
    line_number: Optional[int] = None
    value: Optional[str] = None
    code: Optional[str] = None
    
    def to_dict(self) -> dict:
        effective_rule_id = self.rule_id or self.code
        return {
            # Required output structure (plus backward-compatible aliases)
            "rule_id": effective_rule_id,
            "transaction_type": self.transaction_type,
            "loop_id": self.loop_id or self.loop,
            "message": self.error,
            "suggested_fix": self.suggestion,

            "layer": self.layer.value,
            "type": self.type.value,
            "severity": self.severity.value,
            "segment": self.segment,
            "field": self.field,
            "error": self.error,
            "suggestion": self.suggestion,
            "fixable": self.fixable,
            "loop": self.loop,
            "line_number": self.line_number,
            "value": self.value,
            "code": self.code or effective_rule_id,
        }


@dataclass
class ValidationContext:
    """Context object passed through validation layers"""
    transaction_type: str  # 837P, 835, 834
    edi_data: Dict[str, Any]  # Original parser output
    segments: List[Dict[str, Any]] = field(default_factory=list)  # Flat list of all segments
    loops: List[Dict[str, Any]] = field(default_factory=list)  # Loop structure from parser
    loop_stack: List[str] = field(default_factory=list)
    accumulated_data: Dict[str, Any] = field(default_factory=dict)
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    
    def add_error(self, error: ValidationError):
        """Add error to appropriate list based on severity"""
        if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR]:
            self.errors.append(error)
        else:
            self.warnings.append(error)
    
    def get_element_value(self, segment_id: str, element_position: str, occurrence: int = 0) -> Optional[str]:
        """
        Extract element value from parser segment format
        
        Args:
            segment_id: Segment ID (e.g., "NM1", "DMG")
            element_position: Element position (e.g., "01", "09")
            occurrence: Which occurrence to get (0 = first)
        
        Returns:
            Element value or None
        """
        matching_segments = [s for s in self.segments if s.get("segmentId") == segment_id]
        
        if occurrence < len(matching_segments):
            segment = matching_segments[occurrence]
            if "elements" in segment:
                for element in segment["elements"]:
                    if element.get("position") == element_position:
                        return element.get("value", "")
        
        return None
    
    def get_all_segments(self, segment_id: str) -> List[Dict[str, Any]]:
        """Get all segments of a specific type"""
        return [seg for seg in self.segments if seg.get("segmentId") == segment_id]
    
    def get_all_element_values(self, segment_id: str, element_position: str) -> List[str]:
        """Get all element values for a segment type"""
        values = []
        for segment in self.get_all_segments(segment_id):
            if "elements" in segment:
                for element in segment["elements"]:
                    if element.get("position") == element_position:
                        value = element.get("value", "")
                        if value:
                            values.append(value)
        return values
    
    def count_segments(self, segment_id: str) -> int:
        """Count occurrences of a segment"""
        return len(self.get_all_segments(segment_id))
    
    def find_segment_with_qualifier(self, segment_id: str, qualifier_position: str, qualifier_value: str) -> Optional[Dict[str, Any]]:
        """Find segment with specific qualifier value"""
        for segment in self.get_all_segments(segment_id):
            if "elements" in segment:
                for element in segment["elements"]:
                    if element.get("position") == qualifier_position and element.get("value") == qualifier_value:
                        return segment
        return None


@dataclass
class ValidationResult:
    """Final validation result"""
    status: str  # PASSED, FAILED, PARTIAL
    transaction_type: str
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    context: Optional[ValidationContext] = None
    processing_time: float = 0.0
    fixed_version: Optional[str] = None
    
    @property
    def total_errors(self) -> int:
        return len(self.errors)
    
    @property
    def total_warnings(self) -> int:
        return len(self.warnings)
    
    @property
    def fixable_errors(self) -> int:
        return sum(1 for e in self.errors if e.fixable)
    
    @property
    def critical_errors(self) -> int:
        return sum(1 for e in self.errors if e.severity == ErrorSeverity.CRITICAL)
    
    def get_layer_breakdown(self) -> Dict[str, int]:
        """Count errors by layer"""
        breakdown = {
            "structural": 0,
            "business": 0,
            "external": 0
        }
        for error in self.errors:
            breakdown[error.layer.value.lower()] += 1
        return breakdown
    
    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "transactionType": self.transaction_type,
            "summary": {
                "totalErrors": self.total_errors,
                "totalWarnings": self.total_warnings,
                "fixableErrors": self.fixable_errors,
                "criticalErrors": self.critical_errors,
                "layerBreakdown": self.get_layer_breakdown()
            },
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "processingTime": f"{self.processing_time:.2f}s",
            "fixedVersion": self.fixed_version
        }
