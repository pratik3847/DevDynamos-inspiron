"""
Structural Validator - Layer 1
Validates EDI file structure, segments, and basic syntax
"""
from typing import List, Dict, Any
from ..models import ValidationError, ValidationContext, ErrorSeverity, ErrorLayer, ErrorType


class StructuralValidator:
    """Layer 1: Validates EDI structure and syntax"""
    
    # Required segments for each transaction type
    REQUIRED_SEGMENTS = {
        "837P": ["ISA", "GS", "ST", "BHT", "NM1", "SE", "GE", "IEA"],
        "835": ["ISA", "GS", "ST", "BPR", "SE", "GE", "IEA"],
        "834": ["ISA", "GS", "ST", "BGN", "SE", "GE", "IEA"]
    }
    
    def __init__(self):
        self.errors: List[ValidationError] = []
    
    def validate(self, context: ValidationContext) -> List[ValidationError]:
        """Execute all structural validations"""
        self.errors = []
        
        try:
            # Basic structure checks
            self._validate_envelope_structure(context)
            self._validate_required_segments(context)
            self._validate_segment_structure(context)
            self._validate_control_numbers(context)
            self._validate_segment_counts(context)
            self._validate_group_counts(context)
            self._validate_isa_gs_consistency(context)
            
        except Exception as e:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.STRUCTURAL,
                    type=ErrorType.SEGMENT,
                    severity=ErrorSeverity.CRITICAL,
                    segment="UNKNOWN",
                    error=f"Critical structural validation error: {str(e)}",
                    suggestion="Check if file is properly formatted EDI"
                )
            )
        
        return self.errors

    def _validate_group_counts(self, context: ValidationContext):
        """Validate functional group and interchange group counts.

        - GE01 matches number of ST segments in the GS/GE envelope.
        - IEA01 matches number of GS segments in the ISA/IEA envelope.
        """
        segments = context.segments

        # IEA01 should match number of GS segments
        iea_groups = context.get_element_value("IEA", "01")
        if iea_groups:
            gs_count = sum(1 for s in segments if s.get("segmentId") == "GS")
            try:
                if int(iea_groups) != gs_count:
                    self.errors.append(
                        ValidationError(
                            layer=ErrorLayer.STRUCTURAL,
                            type=ErrorType.CROSS_FIELD,
                            severity=ErrorSeverity.ERROR,
                            segment="IEA",
                            field="IEA01",
                            error=f"IEA functional group count ({iea_groups}) does not match actual GS count ({gs_count})",
                            suggestion=f"Update IEA01 to {gs_count}",
                            fixable=True,
                        )
                    )
            except Exception:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.STRUCTURAL,
                        type=ErrorType.FORMAT,
                        severity=ErrorSeverity.ERROR,
                        segment="IEA",
                        field="IEA01",
                        error=f"IEA01 must be numeric (found '{iea_groups}')",
                        suggestion="Set IEA01 to the number of GS segments in the interchange",
                        fixable=True,
                        value=str(iea_groups),
                    )
                )

        # GE01 should match number of ST segments within each GS/GE block.
        # For now, validate the first GS/GE envelope found.
        gs_index = next((i for i, s in enumerate(segments) if s.get("segmentId") == "GS"), -1)
        ge_index = next((i for i, s in enumerate(segments) if s.get("segmentId") == "GE"), -1)
        ge_count = context.get_element_value("GE", "01")
        if ge_count and gs_index >= 0 and ge_index > gs_index:
            st_count = sum(1 for s in segments[gs_index:ge_index + 1] if s.get("segmentId") == "ST")
            try:
                if int(ge_count) != st_count:
                    self.errors.append(
                        ValidationError(
                            layer=ErrorLayer.STRUCTURAL,
                            type=ErrorType.CROSS_FIELD,
                            severity=ErrorSeverity.ERROR,
                            segment="GE",
                            field="GE01",
                            error=f"GE transaction set count ({ge_count}) does not match actual ST count ({st_count})",
                            suggestion=f"Update GE01 to {st_count}",
                            fixable=True,
                        )
                    )
            except Exception:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.STRUCTURAL,
                        type=ErrorType.FORMAT,
                        severity=ErrorSeverity.ERROR,
                        segment="GE",
                        field="GE01",
                        error=f"GE01 must be numeric (found '{ge_count}')",
                        suggestion="Set GE01 to the number of ST segments in the functional group",
                        fixable=True,
                        value=str(ge_count),
                    )
                )
    
    def _validate_envelope_structure(self, context: ValidationContext):
        """Validate ISA/GS/ST envelope structure"""
        segments = context.segments
        
        if not segments:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.STRUCTURAL,
                    type=ErrorType.SEGMENT,
                    severity=ErrorSeverity.CRITICAL,
                    segment="ISA",
                    error="No segments found in EDI file",
                    suggestion="Ensure file contains valid EDI segments"
                )
            )
            return
        
        # Check ISA segment (must be first)
        if not segments or segments[0].get("segmentId") != "ISA":
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.STRUCTURAL,
                    type=ErrorType.SEGMENT,
                    severity=ErrorSeverity.CRITICAL,
                    segment="ISA",
                    error="ISA segment must be first segment in file",
                    suggestion="Add ISA interchange control header"
                )
            )
        
        # Check IEA segment (must be last)
        if segments and segments[-1].get("segmentId") != "IEA":
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.STRUCTURAL,
                    type=ErrorType.SEGMENT,
                    severity=ErrorSeverity.ERROR,
                    segment="IEA",
                    error="IEA segment must be last segment in file",
                    suggestion="Add IEA interchange control trailer"
                )
            )
        
        # Check for GS/GE pair
        has_gs = any(seg.get("segmentId") == "GS" for seg in segments)
        has_ge = any(seg.get("segmentId") == "GE" for seg in segments)
        
        if has_gs and not has_ge:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.STRUCTURAL,
                    type=ErrorType.SEGMENT,
                    severity=ErrorSeverity.ERROR,
                    segment="GE",
                    error="GS segment found but missing GE trailer",
                    suggestion="Add GE functional group trailer"
                )
            )
        
        # Check for ST/SE pair
        has_st = any(seg.get("segmentId") == "ST" for seg in segments)
        has_se = any(seg.get("segmentId") == "SE" for seg in segments)
        
        if has_st and not has_se:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.STRUCTURAL,
                    type=ErrorType.SEGMENT,
                    severity=ErrorSeverity.ERROR,
                    segment="SE",
                    error="ST segment found but missing SE trailer",
                    suggestion="Add SE transaction set trailer"
                )
            )
    
    def _validate_required_segments(self, context: ValidationContext):
        """Check if all required segments are present"""
        transaction_type = context.transaction_type
        required = self.REQUIRED_SEGMENTS.get(transaction_type, [])
        
        segment_ids = {seg.get("segmentId") for seg in context.segments}
        
        for required_seg in required:
            if required_seg not in segment_ids:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.STRUCTURAL,
                        type=ErrorType.SEGMENT,
                        severity=ErrorSeverity.ERROR,
                        segment=required_seg,
                        error=f"Required segment {required_seg} is missing",
                        suggestion=f"Add {required_seg} segment to transaction"
                    )
                )
    
    def _validate_segment_structure(self, context: ValidationContext):
        """Validate individual segment structure"""
        for idx, segment in enumerate(context.segments):
            segment_id = segment.get("segmentId")
            
            if not segment_id:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.STRUCTURAL,
                        type=ErrorType.SEGMENT,
                        severity=ErrorSeverity.ERROR,
                        segment="UNKNOWN",
                        line_number=idx + 1,
                        error="Segment missing identifier",
                        suggestion="Ensure segment has valid ID"
                    )
                )
                continue
            
            # Check minimum element count for critical segments
            element_count = len(segment.get("elements", []))
            
            if segment_id == "ISA" and element_count < 16:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.STRUCTURAL,
                        type=ErrorType.SEGMENT,
                        severity=ErrorSeverity.CRITICAL,
                        segment="ISA",
                        line_number=idx + 1,
                        error=f"ISA segment must have 16 elements (found {element_count})",
                        suggestion="Verify ISA segment structure"
                    )
                )
            
            elif segment_id == "GS" and element_count < 8:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.STRUCTURAL,
                        type=ErrorType.SEGMENT,
                        severity=ErrorSeverity.ERROR,
                        segment="GS",
                        line_number=idx + 1,
                        error=f"GS segment must have 8 elements (found {element_count})",
                        suggestion="Verify GS segment structure"
                    )
                )
    
    def _validate_control_numbers(self, context: ValidationContext):
        """Validate control numbers match between headers and trailers"""
        # ISA/IEA control number
        isa_control = context.get_element_value("ISA", "13")
        iea_control = context.get_element_value("IEA", "02")
        
        if isa_control and iea_control and isa_control != iea_control:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.STRUCTURAL,
                    type=ErrorType.CROSS_FIELD,
                    severity=ErrorSeverity.ERROR,
                    segment="IEA",
                    field="IEA02",
                    error=f"IEA control number ({iea_control}) does not match ISA ({isa_control})",
                    suggestion="Ensure ISA13 and IEA02 have matching control numbers"
                )
            )
        
        # GS/GE control number
        gs_control = context.get_element_value("GS", "06")
        ge_control = context.get_element_value("GE", "02")
        
        if gs_control and ge_control and gs_control != ge_control:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.STRUCTURAL,
                    type=ErrorType.CROSS_FIELD,
                    severity=ErrorSeverity.ERROR,
                    segment="GE",
                    field="GE02",
                    error=f"GE control number ({ge_control}) does not match GS ({gs_control})",
                    suggestion="Ensure GS06 and GE02 have matching control numbers"
                )
            )
        
        # ST/SE control number
        st_control = context.get_element_value("ST", "02")
        se_control = context.get_element_value("SE", "02")
        
        if st_control and se_control and st_control != se_control:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.STRUCTURAL,
                    type=ErrorType.CROSS_FIELD,
                    severity=ErrorSeverity.ERROR,
                    segment="SE",
                    field="SE02",
                    error=f"SE control number ({se_control}) does not match ST ({st_control})",
                    suggestion="Ensure ST02 and SE02 have matching control numbers"
                )
            )
    
    def _validate_segment_counts(self, context: ValidationContext):
        """Validate segment counts in trailers"""
        # Count segments between ST and SE
        st_index = -1
        se_index = -1
        
        for idx, seg in enumerate(context.segments):
            if seg.get("segmentId") == "ST":
                st_index = idx
            elif seg.get("segmentId") == "SE":
                se_index = idx
                break
        
        if st_index >= 0 and se_index > st_index:
            # Count segments between ST and SE (inclusive)
            actual_count = se_index - st_index + 1
            se_count = context.get_element_value("SE", "01")
            
            if se_count and str(actual_count) != str(se_count):
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.STRUCTURAL,
                        type=ErrorType.CROSS_FIELD,
                        severity=ErrorSeverity.ERROR,
                        segment="SE",
                        field="SE01",
                        error=f"SE segment count ({se_count}) does not match actual count ({actual_count})",
                        suggestion=f"Update SE01 to {actual_count}",
                        fixable=True
                    )
                )
    
    def _validate_isa_gs_consistency(self, context: ValidationContext):
        """Validate ISA and GS version consistency"""
        # ISA12 - Interchange Control Version Number
        isa_version = context.get_element_value("ISA", "12")
        
        # GS08 - Version/Release/Industry Identifier Code
        gs_version = context.get_element_value("GS", "08")
        
        if isa_version and gs_version:
            # Clean ISA version (may have extra characters like ^)
            isa_clean = isa_version.split("^")[-1] if "^" in isa_version else isa_version
            
            # Check if ISA version is valid
            if isa_clean not in ["00401", "00501"]:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.STRUCTURAL,
                        type=ErrorType.FORMAT,
                        severity=ErrorSeverity.ERROR,
                        segment="ISA",
                        field="ISA12",
                        error=f"Invalid ISA version: {isa_version}",
                        suggestion="Use valid version (00401 or 00501)",
                        fixable=False,
                        value=isa_version
                    )
                )
            
            # Check if GS version matches ISA version
            # ISA 00501 should match GS 005010X... format
            if isa_clean == "00501" and not gs_version.startswith("00501"):
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.STRUCTURAL,
                        type=ErrorType.CROSS_FIELD,
                        severity=ErrorSeverity.ERROR,
                        segment="GS",
                        field="GS08",
                        error=f"GS version ({gs_version}) does not match ISA version ({isa_version})",
                        suggestion="Ensure ISA12 and GS08 versions are consistent (e.g., ISA=00501, GS=005010X220A1)",
                        fixable=False
                    )
                )
            elif isa_clean == "00401" and not gs_version.startswith("00401"):
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.STRUCTURAL,
                        type=ErrorType.CROSS_FIELD,
                        severity=ErrorSeverity.ERROR,
                        segment="GS",
                        field="GS08",
                        error=f"GS version ({gs_version}) does not match ISA version ({isa_version})",
                        suggestion="Ensure ISA12 and GS08 versions are consistent (e.g., ISA=00401, GS=004010X098A1)",
                        fixable=False
                    )
                )
