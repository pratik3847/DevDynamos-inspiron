"""
Business Validator - Layer 2
Validates business rules, formats, qualifiers, and cross-field consistency
"""
from typing import List
from ..models import ValidationError, ValidationContext, ErrorSeverity, ErrorLayer, ErrorType
from ..formats import (
    NPIValidator, DateValidator, AmountValidator,
    ZIPCodeValidator, ProcedureCodeValidator, ICD10Validator
)
from ..reference_data import get_code_set_loader


class BusinessValidator:
    """Layer 2: Validates business rules and data formats"""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.code_loader = get_code_set_loader()
    
    def validate(self, context: ValidationContext) -> List[ValidationError]:
        """Execute all business validations"""
        self.errors = []
        
        try:
            # Format validations
            self._validate_npi_fields(context)
            self._validate_date_fields(context)
            self._validate_amount_fields(context)
            self._validate_zip_codes(context)
            
            # Qualifier validations
            self._validate_qualifiers(context)
            
            # Cross-field validations
            self._validate_cross_field_consistency(context)
            
            # Transaction-specific validations
            if context.transaction_type in ("837P", "837"):
                self._validate_837_specific(context)
            elif context.transaction_type == "835":
                self._validate_835_specific(context)
            elif context.transaction_type == "834":
                self._validate_834_specific(context)
            
        except Exception as e:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.BUSINESS,
                    type=ErrorType.CROSS_FIELD,
                    severity=ErrorSeverity.ERROR,
                    segment="UNKNOWN",
                    error=f"Business validation error: {str(e)}",
                    suggestion="Review business rule validation logic"
                )
            )
        
        return self.errors
    
    def _validate_npi_fields(self, context: ValidationContext):
        """Validate all NPI fields in the transaction"""
        # Find all NM1 segments
        nm1_segments = context.get_all_segments("NM1")
        
        for idx, segment in enumerate(nm1_segments):
            # Get qualifier and ID value
            qualifier = None
            id_value = None
            
            if "elements" in segment:
                for element in segment["elements"]:
                    if element.get("position") == "08":
                        qualifier = element.get("value")
                    elif element.get("position") == "09":
                        id_value = element.get("value")
            
            # If we have a 10-digit numeric ID, it should be an NPI
            if id_value and len(id_value) == 10 and id_value.isdigit():
                # Validate NPI format and Luhn checksum
                is_valid, error_msg = NPIValidator.validate(id_value)
                
                if not is_valid:
                    self.errors.append(
                        ValidationError(
                            layer=ErrorLayer.BUSINESS,
                            type=ErrorType.FORMAT,
                            severity=ErrorSeverity.ERROR,
                            segment="NM1",
                            field="NM109",
                            error=error_msg,
                            suggestion=NPIValidator.get_suggestion(id_value),
                            fixable=False,
                            value=id_value,
                            code="NPI001"
                        )
                    )
    
    def _validate_date_fields(self, context: ValidationContext):
        """Validate all date fields"""
        # DTP segments contain dates
        dtp_segments = context.get_all_segments("DTP")
        
        for segment in dtp_segments:
            date_qualifier = None
            date_format = None
            date_value = None
            
            if "elements" in segment:
                for element in segment["elements"]:
                    pos = element.get("position")
                    if pos == "01":
                        date_qualifier = element.get("value")
                    elif pos == "02":
                        date_format = element.get("value")
                    elif pos == "03":
                        date_value = element.get("value")
            
            if date_value:
                # Determine if future dates are allowed
                # Most dates should NOT be in the future
                # Only allow future for specific qualifiers like effective dates
                future_allowed_qualifiers = ["303", "348", "349"]  # Future effective dates
                allow_future = date_qualifier in future_allowed_qualifiers
                check_dob = date_qualifier == "291"  # 291 = DOB
                
                format_type = "CCYYMMDD" if date_format == "D8" else "CCYYMMDD"
                
                is_valid, error_msg = DateValidator.validate(
                    date_value, 
                    format_type=format_type,
                    allow_future=allow_future,
                    check_dob=check_dob
                )
                
                if not is_valid:
                    self.errors.append(
                        ValidationError(
                            layer=ErrorLayer.BUSINESS,
                            type=ErrorType.FORMAT,
                            severity=ErrorSeverity.ERROR,
                            segment="DTP",
                            field="DTP03",
                            error=error_msg,
                            suggestion=DateValidator.get_suggestion(date_value, format_type),
                            fixable=True,
                            value=date_value,
                            code="DATE001"
                        )
                    )
        
        # DMG02 contains date of birth
        dmg_segments = context.get_all_segments("DMG")
        
        for segment in dmg_segments:
            dob = None
            
            if "elements" in segment:
                for element in segment["elements"]:
                    if element.get("position") == "02":
                        dob = element.get("value")
                        break
            
            if dob:
                is_valid, error_msg = DateValidator.validate(
                    dob, 
                    format_type="CCYYMMDD",
                    allow_future=False,
                    check_dob=True
                )
                
                if not is_valid:
                    self.errors.append(
                        ValidationError(
                            layer=ErrorLayer.BUSINESS,
                            type=ErrorType.FORMAT,
                            severity=ErrorSeverity.ERROR,
                            segment="DMG",
                            field="DMG02",
                            error=error_msg,
                            suggestion="Verify date of birth is in CCYYMMDD format and reasonable",
                            fixable=False,
                            value=dob,
                            code="DATE002"
                        )
                    )
    
    def _validate_amount_fields(self, context: ValidationContext):
        """Validate monetary amount fields"""
        # CLM02 - Total claim charge amount
        clm_segments = context.get_all_segments("CLM")
        
        for segment in clm_segments:
            amount = context.get_element_value("CLM", "02")
            
            if amount:
                is_valid, error_msg = AmountValidator.validate(
                    amount,
                    allow_negative=False,
                    allow_zero=False
                )
                
                if not is_valid:
                    self.errors.append(
                        ValidationError(
                            layer=ErrorLayer.BUSINESS,
                            type=ErrorType.FORMAT,
                            severity=ErrorSeverity.ERROR,
                            segment="CLM",
                            field="CLM02",
                            error=error_msg,
                            suggestion=AmountValidator.get_suggestion(amount),
                            fixable=True,
                            value=amount,
                            code="AMT001"
                        )
                    )
    
    def _validate_zip_codes(self, context: ValidationContext):
        """Validate ZIP code fields"""
        n4_segments = context.get_all_segments("N4")
        
        for segment in n4_segments:
            zip_code = None
            
            if "elements" in segment:
                for element in segment["elements"]:
                    if element.get("position") == "03":
                        zip_code = element.get("value")
                        break
            
            if zip_code:
                is_valid, error_msg = ZIPCodeValidator.validate(zip_code)
                
                if not is_valid:
                    self.errors.append(
                        ValidationError(
                            layer=ErrorLayer.BUSINESS,
                            type=ErrorType.FORMAT,
                            severity=ErrorSeverity.ERROR,
                            segment="N4",
                            field="N403",
                            error=error_msg,
                            suggestion="ZIP code must be 5 digits (XXXXX) or 9 digits with hyphen (XXXXX-XXXX)",
                            fixable=True,
                            value=zip_code,
                            code="ZIP001"
                        )
                    )
    
    def _validate_qualifiers(self, context: ValidationContext):
        """Validate qualifier codes using reference data + transaction context.

        Context-aware NM108 rules (do NOT apply a global 'invalid qualifier' check blindly):
        - NM1*85 (Billing Provider) -> NM108 must be XX
        - NM1*82 (Rendering Provider) -> NM108 must be XX
        - NM1*IL (Subscriber) -> NM108 may be MI
        - NM1*41 / NM1*40 (Submitter/Receiver) -> NM108 may be 46
        """
        valid_nm108_all = self.code_loader.get_qualifier_values("NM108")
        nm1_segments = context.get_all_segments("NM1")

        for segment in nm1_segments:
            nm101 = None
            qualifier = None
            id_value = None

            for element in segment.get("elements", []) or []:
                pos = element.get("position")
                if pos == "01":
                    nm101 = element.get("value")
                elif pos == "08":
                    qualifier = element.get("value")
                elif pos == "09":
                    id_value = element.get("value")

            if not qualifier or not id_value:
                continue

            allowed_by_context = None
            if nm101 in ("85", "82"):
                allowed_by_context = {"XX"}
            elif nm101 == "IL":
                allowed_by_context = {"MI"}
            elif nm101 in ("41", "40"):
                allowed_by_context = {"46"}

            if allowed_by_context is not None:
                if qualifier not in allowed_by_context:
                    self.errors.append(
                        ValidationError(
                            layer=ErrorLayer.BUSINESS,
                            type=ErrorType.CODE,
                            severity=ErrorSeverity.ERROR,
                            segment="NM1",
                            field="NM108",
                            error=f"NM108 qualifier '{qualifier}' is not allowed for NM101={nm101}",
                            suggestion=f"Use {', '.join(sorted(allowed_by_context))} for this NM1 context",
                            fixable=False,
                            value=qualifier,
                            code="NM108_CTX001",
                        )
                    )
                # If context says it's allowed, do not apply global invalid-qualifier rules.
                continue

            # Default/global rules (fallback when no context mapping is defined)
            id_length = len(id_value)
            is_numeric = id_value.isdigit()

            if id_length == 10 and is_numeric and qualifier != "XX":
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.ERROR,
                        segment="NM1",
                        field="NM108",
                        error=f"Invalid qualifier '{qualifier}' for 10-digit ID",
                        suggestion="Use XX for 10-digit NPI (National Provider Identifier)",
                        fixable=False,
                        value=qualifier,
                        code="QUAL001",
                    )
                )

            if qualifier == "XX" and (id_length != 10 or not is_numeric):
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.ERROR,
                        segment="NM1",
                        field="NM109",
                        error=f"Invalid NPI format: {id_value} (length: {id_length})",
                        suggestion="NPI must be exactly 10 numeric digits when using qualifier XX",
                        fixable=False,
                        value=id_value,
                        code="QUAL003",
                    )
                )

            if qualifier == "34" and (id_length != 9 or not is_numeric):
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.WARNING,
                        segment="NM1",
                        field="NM109",
                        error=f"SSN format issue: {id_value} (length: {id_length})",
                        suggestion="SSN should be 9 numeric digits when using qualifier 34",
                        fixable=False,
                        value=id_value,
                        code="QUAL004",
                    )
                )

            # Do NOT globally mark '46' as invalid; warn only if unknown context.
            if qualifier == "46":
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.WARNING,
                        segment="NM1",
                        field="NM108",
                        error="NM108 qualifier '46' is typically used for Submitter/Receiver identifiers",
                        suggestion="If this is Submitter/Receiver (NM101=41/40), this qualifier is expected",
                        fixable=False,
                        value=qualifier,
                        code="NM108_WARN046",
                    )
                )
                continue

            if valid_nm108_all and qualifier not in valid_nm108_all:
                valid_list = ", ".join(sorted(valid_nm108_all)[:5])
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.ERROR,
                        segment="NM1",
                        field="NM108",
                        error=f"Invalid identification code qualifier: {qualifier}",
                        suggestion=f"Use valid qualifier (e.g., {valid_list})",
                        fixable=False,
                        value=qualifier,
                        code="QUAL002",
                    )
                )
    
    def _validate_cross_field_consistency(self, context: ValidationContext):
        """Validate consistency across fields"""
        # DOB vs Claim Date
        dob = context.get_element_value("DMG", "02")
        
        # Find service date from DTP segment with qualifier 472 (service date)
        claim_date = None
        dtp_segments = context.get_all_segments("DTP")
        for segment in dtp_segments:
            qualifier = None
            date_value = None
            
            if "elements" in segment:
                for element in segment["elements"]:
                    if element.get("position") == "01":
                        qualifier = element.get("value")
                    elif element.get("position") == "03":
                        date_value = element.get("value")
            
            if qualifier == "472":  # Service date
                claim_date = date_value
                break
        
        if dob and claim_date:
            comparison = DateValidator.compare_dates(dob, claim_date)
            if comparison is not None and comparison >= 0:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.CROSS_FIELD,
                        severity=ErrorSeverity.ERROR,
                        segment="DTP",
                        field="DTP03",
                        error="Service date must be after patient date of birth",
                        suggestion="Verify patient DOB and service date are correct",
                        fixable=False,
                        code="CROSS001"
                    )
                )
    
    def _validate_837_specific(self, context: ValidationContext):
        """837-specific validations (transaction/loop aware, best-effort without full loop modeling)."""
        # Per-claim required segments/loops (approximate Loop 2300/2400 boundaries by CLM..next CLM)
        segments = context.segments
        clm_indexes = [i for i, s in enumerate(segments) if s.get("segmentId") == "CLM"]

        if not clm_indexes:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.BUSINESS,
                    type=ErrorType.SEGMENT,
                    severity=ErrorSeverity.ERROR,
                    segment="CLM",
                    error="837 transaction must contain at least one CLM (Claim Information) segment",
                    suggestion="Add a CLM segment for each claim (Loop 2300)",
                    fixable=False,
                    loop="2300",
                    code="837_REQ_CLM",
                )
            )
            return

        # Bound each claim block to next CLM or SE
        se_index = next((i for i, s in enumerate(segments) if s.get("segmentId") == "SE"), len(segments))
        for idx, start in enumerate(clm_indexes):
            end = clm_indexes[idx + 1] if idx + 1 < len(clm_indexes) else se_index
            block = segments[start:end]

            # Claim total vs sum(service lines) within this claim block
            clm_total = None
            for e in segments[start].get("elements", []) or []:
                if e.get("position") == "02":
                    clm_total = e.get("value")
                    break

            service_total = 0
            for s in block:
                if s.get("segmentId") != "SV1":
                    continue
                for e in s.get("elements", []) or []:
                    if e.get("position") == "02":
                        amt = e.get("value")
                        if not amt:
                            continue
                        parsed = AmountValidator.parse_amount(str(amt))
                        if parsed:
                            service_total += parsed

            if clm_total:
                clm_parsed = AmountValidator.parse_amount(str(clm_total))
                if clm_parsed is not None and service_total > 0:
                    if not AmountValidator.compare_amounts(str(clm_parsed), str(service_total)):
                        self.errors.append(
                            ValidationError(
                                layer=ErrorLayer.BUSINESS,
                                type=ErrorType.CROSS_FIELD,
                                severity=ErrorSeverity.ERROR,
                                segment="CLM",
                                field="CLM02",
                                error=f"Claim total (${clm_parsed}) does not match sum of service lines (${service_total})",
                                suggestion="Ensure CLM02 equals sum of all SV102 amounts within the claim",
                                fixable=True,
                                loop="2300",
                                code="837_CLM_TOTAL001",
                            )
                        )

            has_hi = any(s.get("segmentId") == "HI" for s in block)
            has_dtp_472 = False
            has_sv = any(s.get("segmentId") in ("SV1", "SV2") for s in block)
            has_nm1_82 = False

            for s in block:
                if s.get("segmentId") == "DTP":
                    q = None
                    for e in s.get("elements", []) or []:
                        if e.get("position") == "01":
                            q = e.get("value")
                            break
                    if q == "472":
                        has_dtp_472 = True
                if s.get("segmentId") == "NM1":
                    for e in s.get("elements", []) or []:
                        if e.get("position") == "01" and e.get("value") == "82":
                            has_nm1_82 = True
                            break

            if not has_hi:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.SEGMENT,
                        severity=ErrorSeverity.ERROR,
                        segment="HI",
                        error="Each claim must include diagnosis codes (HI segment)",
                        suggestion="Add HI segment in Loop 2300 with ICD-10 diagnosis codes",
                        fixable=False,
                        loop="2300",
                        code="837_REQ_HI",
                    )
                )

            if not has_dtp_472:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.SEGMENT,
                        severity=ErrorSeverity.ERROR,
                        segment="DTP",
                        field="DTP01",
                        error="Each claim must include a service date (DTP*472)",
                        suggestion="Add DTP segment with qualifier 472 and a valid date",
                        fixable=True,
                        loop="2300",
                        code="837_REQ_DTP472",
                    )
                )

            if not has_sv:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.LOOP,
                        severity=ErrorSeverity.ERROR,
                        segment="SV1",
                        error="Each claim must have at least one service line (Loop 2400)",
                        suggestion="Add at least one SV1/SV2 service line segment",
                        fixable=False,
                        loop="2400",
                        code="837_REQ_2400",
                    )
                )

            if not has_nm1_82:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.LOOP,
                        severity=ErrorSeverity.ERROR,
                        segment="NM1",
                        field="NM101",
                        error="837 claims must include Rendering Provider (NM1*82)",
                        suggestion="Add NM1 segment with NM101=82 in the Rendering Provider loop (2310B)",
                        fixable=False,
                        loop="2310B",
                        code="837_REQ_NM182",
                    )
                )

        # Diagnosis code format validation: HI composites should contain ICD-10 codes
        for hi in context.get_all_segments("HI"):
            for element in hi.get("elements", []) or []:
                raw = element.get("value")
                if not raw:
                    continue
                # Common patterns: ABK:K35.2 or BK:K35.2
                parts = str(raw).split(":")
                diag = parts[-1].strip().upper() if parts else ""
                if not diag:
                    continue
                ok, msg = ICD10Validator.validate(diag)
                if not ok:
                    self.errors.append(
                        ValidationError(
                            layer=ErrorLayer.BUSINESS,
                            type=ErrorType.FORMAT,
                            severity=ErrorSeverity.ERROR,
                            segment="HI",
                            error=f"Invalid ICD-10 diagnosis code format: {diag}",
                            suggestion="Use ICD-10 format like J44.9 (decimal required for 4+ chars)",
                            fixable=False,
                            value=diag,
                            code="ICD10_FMT001",
                        )
                    )

        # Procedure code validation: SV101 usually contains qualifier+code like HC:99213
        for sv in context.get_all_segments("SV1"):
            comp = None
            for e in sv.get("elements", []) or []:
                if e.get("position") == "01":
                    comp = e.get("value")
                    break
            if not comp:
                continue
            code_part = str(comp).split(":")[-1].strip().upper()
            ok, msg = ProcedureCodeValidator.validate(code_part)
            if not ok:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.FORMAT,
                        severity=ErrorSeverity.ERROR,
                        segment="SV1",
                        field="SV101",
                        error=f"Invalid procedure code format: {code_part}",
                        suggestion="Use a valid 5-character CPT/HCPCS code",
                        fixable=False,
                        value=code_part,
                        code="PROC_FMT001",
                    )
                )


    
    def _validate_835_specific(self, context: ValidationContext):
        """835-specific validations"""
        # Required CLP presence
        if not context.get_all_segments("CLP"):
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.BUSINESS,
                    type=ErrorType.SEGMENT,
                    severity=ErrorSeverity.ERROR,
                    segment="CLP",
                    error="835 transaction must contain at least one CLP (Claim Payment) segment",
                    suggestion="Add CLP segments for each claim payment",
                    fixable=False,
                    loop="2100",
                    code="835_REQ_CLP",
                )
            )

        # Validate payer/payee identification loops (approx via N1)
        n1_segments = context.get_all_segments("N1")
        n1_codes = []
        for n1 in n1_segments:
            code = None
            for e in n1.get("elements", []) or []:
                if e.get("position") == "01":
                    code = e.get("value")
                    break
            if code:
                n1_codes.append(code)
        if "PR" not in n1_codes:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.BUSINESS,
                    type=ErrorType.LOOP,
                    severity=ErrorSeverity.ERROR,
                    segment="N1",
                    field="N101",
                    error="Missing payer identification loop (1000A): N1*PR",
                    suggestion="Add N1 segment with N101=PR for the payer",
                    fixable=False,
                    loop="1000A",
                    code="835_REQ_1000A",
                )
            )
        if "PE" not in n1_codes:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.BUSINESS,
                    type=ErrorType.LOOP,
                    severity=ErrorSeverity.ERROR,
                    segment="N1",
                    field="N101",
                    error="Missing payee identification loop (1000B): N1*PE",
                    suggestion="Add N1 segment with N101=PE for the payee",
                    fixable=False,
                    loop="1000B",
                    code="835_REQ_1000B",
                )
            )

        # Validate CAS segment group codes
        valid_group_codes = ["CO", "PR", "OA", "PI", "CR"]
        
        cas_segments = context.get_all_segments("CAS")
        
        for segment in cas_segments:
            group_code = None
            
            if "elements" in segment:
                for element in segment["elements"]:
                    if element.get("position") == "01":
                        group_code = element.get("value")
                        break
            
            if group_code and group_code not in valid_group_codes:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.ERROR,
                        segment="CAS",
                        field="CAS01",
                        error=f"Invalid CAS group code: {group_code}",
                        suggestion=f"Use valid group code: {', '.join(valid_group_codes)}",
                        fixable=False,
                        value=group_code,
                        code="835001"
                    )
                )

            # Validate CARC codes (reason codes) exist
            # CAS segments repeat in groups of 3: reason code, amount, quantity
            if group_code:
                elements = segment.get("elements", []) or []
                for element in elements:
                    pos = element.get("position")
                    if pos in ("02", "05", "08", "11", "14", "17"):
                        reason = (element.get("value") or "").strip()
                        if reason and not self.code_loader.is_valid_carc(reason):
                            self.errors.append(
                                ValidationError(
                                    layer=ErrorLayer.BUSINESS,
                                    type=ErrorType.CODE,
                                    severity=ErrorSeverity.ERROR,
                                    segment="CAS",
                                    field=f"CAS{pos}",
                                    error=f"Invalid CARC adjustment reason code: {reason}",
                                    suggestion="Use a valid CARC code",
                                    fixable=False,
                                    value=reason,
                                    code="835_CARC001",
                                )
                            )

        # Per-CLP block checks: if paid < charged -> CAS required; and Paid + PR <= Charged
        segments = context.segments
        clp_indexes = [i for i, s in enumerate(segments) if s.get("segmentId") == "CLP"]
        se_index = next((i for i, s in enumerate(segments) if s.get("segmentId") == "SE"), len(segments))
        for idx, start in enumerate(clp_indexes):
            end = clp_indexes[idx + 1] if idx + 1 < len(clp_indexes) else se_index
            block = segments[start:end]

            clp = segments[start]
            charged = None
            paid = None
            patient_resp = None
            for e in clp.get("elements", []) or []:
                if e.get("position") == "03":
                    charged = e.get("value")
                elif e.get("position") == "04":
                    paid = e.get("value")
                elif e.get("position") == "05":
                    patient_resp = e.get("value")

            charged_amt = AmountValidator.parse_amount(charged) if charged else None
            paid_amt = AmountValidator.parse_amount(paid) if paid else None
            pr_amt = AmountValidator.parse_amount(patient_resp) if patient_resp else 0

            has_cas = any(s.get("segmentId") == "CAS" for s in block)
            if charged_amt is not None and paid_amt is not None and paid_amt < charged_amt and not has_cas:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.SEGMENT,
                        severity=ErrorSeverity.ERROR,
                        segment="CAS",
                        error="CAS segment is required when paid amount is less than charged amount",
                        suggestion="Add CAS adjustments explaining the difference between charged and paid",
                        fixable=False,
                        loop="2110",
                        code="835_REQ_CAS",
                    )
                )

            if charged_amt is not None and paid_amt is not None:
                total = paid_amt + (pr_amt or 0)
                if total > charged_amt + 0.01:
                    self.errors.append(
                        ValidationError(
                            layer=ErrorLayer.BUSINESS,
                            type=ErrorType.CROSS_FIELD,
                            severity=ErrorSeverity.ERROR,
                            segment="CLP",
                            error="Paid amount + patient responsibility cannot exceed charged amount",
                            suggestion="Verify CLP03 (charged), CLP04 (paid), and CLP05 (patient responsibility)",
                            fixable=False,
                            loop="2100",
                            code="835_AMT001",
                        )
                    )
    
    def _check_duplicate_members(self, context: ValidationContext):
        """Check for duplicate members in 834 transaction"""
        # Track members by SSN, Member ID, and Name+DOB
        seen_members = {}
        
        # Get all NM1 loops (member loops)
        nm1_segments = context.get_all_segments("NM1")
        
        for idx, nm1_segment in enumerate(nm1_segments):
            # Extract member identifiers
            member_id = None
            last_name = None
            first_name = None
            dob = None
            
            if "elements" in nm1_segment:
                for element in nm1_segment["elements"]:
                    pos = element.get("position")
                    if pos == "03":
                        last_name = element.get("value")
                    elif pos == "04":
                        first_name = element.get("value")
                    elif pos == "09":
                        member_id = element.get("value")
            
            # Find associated DMG segment for DOB
            # In 834, DMG follows NM1 in the same loop
            if idx < len(context.segments):
                for i in range(idx, min(idx + 10, len(context.segments))):
                    seg = context.segments[i]
                    if seg.get("segmentId") == "DMG":
                        if "elements" in seg:
                            for element in seg["elements"]:
                                if element.get("position") == "02":
                                    dob = element.get("value")
                                    break
                        break
            
            # Create unique key from available identifiers
            if member_id or (last_name and first_name and dob):
                # Check by member ID
                if member_id:
                    if member_id in seen_members:
                        self.errors.append(
                            ValidationError(
                                layer=ErrorLayer.BUSINESS,
                                type=ErrorType.CROSS_FIELD,
                                severity=ErrorSeverity.ERROR,
                                segment="NM1",
                                field="NM109",
                                error=f"Duplicate member ID detected: {member_id}",
                                suggestion="Each member must have a unique identifier",
                                fixable=False,
                                value=member_id,
                                code="834003"
                            )
                        )
                    else:
                        seen_members[member_id] = True
                
                # Check by name + DOB combination
                if last_name and first_name and dob:
                    name_dob_key = f"{last_name}|{first_name}|{dob}"
                    if name_dob_key in seen_members:
                        self.errors.append(
                            ValidationError(
                                layer=ErrorLayer.BUSINESS,
                                type=ErrorType.CROSS_FIELD,
                                severity=ErrorSeverity.WARNING,
                                segment="NM1",
                                error=f"Possible duplicate member: {first_name} {last_name} (DOB: {dob})",
                                suggestion="Verify this is not a duplicate enrollment",
                                fixable=False,
                                code="834004"
                            )
                        )
                    else:
                        seen_members[name_dob_key] = True
    
    def _validate_834_specific(self, context: ValidationContext):
        """834-specific validations using reference data"""
        # Required member loop (INS)
        ins_segments = context.get_all_segments("INS")
        if not ins_segments:
            self.errors.append(
                ValidationError(
                    layer=ErrorLayer.BUSINESS,
                    type=ErrorType.LOOP,
                    severity=ErrorSeverity.ERROR,
                    segment="INS",
                    error="834 transaction must contain member loops (INS segments in Loop 2000)",
                    suggestion="Add INS segments for each subscriber/dependent",
                    fixable=False,
                    loop="2000",
                    code="834_REQ_INS",
                )
            )
            return

        # Hierarchy validation: dependents must follow a subscriber
        seen_subscriber = False

        # Iterate INS blocks for per-member required segments
        segments = context.segments
        ins_indexes = [i for i, s in enumerate(segments) if s.get("segmentId") == "INS"]
        se_index = next((i for i, s in enumerate(segments) if s.get("segmentId") == "SE"), len(segments))

        for idx, start in enumerate(ins_indexes):
            end = ins_indexes[idx + 1] if idx + 1 < len(ins_indexes) else se_index
            block = segments[start:end]

            # INS02 relationship code determines subscriber vs dependent (18=Self is typical subscriber)
            ins02 = None
            ins03 = None  # maintenance type code
            for e in segments[start].get("elements", []) or []:
                if e.get("position") == "02":
                    ins02 = e.get("value")
                elif e.get("position") == "03":
                    ins03 = e.get("value")

            if ins02 == "18":
                seen_subscriber = True
            else:
                if not seen_subscriber:
                    self.errors.append(
                        ValidationError(
                            layer=ErrorLayer.BUSINESS,
                            type=ErrorType.SEQUENCE,
                            severity=ErrorSeverity.ERROR,
                            segment="INS",
                            field="INS02",
                            error="Dependent record appears before any subscriber record",
                            suggestion="Ensure subscriber (INS02=18) appears before dependent loops",
                            fixable=False,
                            loop="2000",
                            code="834_HIER001",
                        )
                    )

            # Require REF (Subscriber ID) within member loop (best-effort: REF01=0F or 1L)
            has_ref_sub_id = False
            for s in block:
                if s.get("segmentId") != "REF":
                    continue
                ref01 = None
                for e in s.get("elements", []) or []:
                    if e.get("position") == "01":
                        ref01 = e.get("value")
                        break
                if ref01 in ("0F", "1L"):
                    has_ref_sub_id = True
                    break
            if not has_ref_sub_id:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.SEGMENT,
                        severity=ErrorSeverity.ERROR,
                        segment="REF",
                        error="Member loop must include Subscriber ID (REF segment)",
                        suggestion="Add REF*0F (Subscriber Number) or REF*1L as applicable",
                        fixable=False,
                        loop="2000",
                        code="834_REQ_REF",
                    )
                )

            # Require DTP*348 Effective Date within member loop
            effective_date = None
            for s in block:
                if s.get("segmentId") != "DTP":
                    continue
                q = None
                val = None
                for e in s.get("elements", []) or []:
                    if e.get("position") == "01":
                        q = e.get("value")
                    elif e.get("position") == "03":
                        val = e.get("value")
                if q == "348" and val:
                    effective_date = val
                    break
            if not effective_date:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.SEGMENT,
                        severity=ErrorSeverity.ERROR,
                        segment="DTP",
                        field="DTP01",
                        error="Member loop must include effective date (DTP*348)",
                        suggestion="Add DTP segment with qualifier 348 and a valid date",
                        fixable=True,
                        loop="2000",
                        code="834_REQ_DTP348",
                    )
                )

            # Maintenance type vs effective date (basic retroactive heuristic)
            if ins03 == "021" and effective_date:
                # If effective date is in the past, '021' (Addition) is usually suspicious.
                ok, _ = DateValidator.validate(effective_date, format_type="CCYYMMDD", allow_future=True)
                if ok:
                    try:
                        from datetime import datetime

                        eff = datetime.strptime(effective_date[:8], "%Y%m%d").date()
                        today = datetime.utcnow().date()
                        if eff < today:
                            self.errors.append(
                                ValidationError(
                                    layer=ErrorLayer.BUSINESS,
                                    type=ErrorType.CROSS_FIELD,
                                    severity=ErrorSeverity.WARNING,
                                    segment="INS",
                                    field="INS03",
                                    error="Retroactive effective date typically should not use maintenance type '021'",
                                    suggestion="Confirm INS03 maintenance type is correct for this effective date",
                                    fixable=False,
                                    loop="2000",
                                    code="834_MAINT001",
                                )
                            )
                    except Exception:
                        pass

        # Validate INS segment codes
        valid_ins01 = self.code_loader.get_qualifier_values("INS01")
        valid_ins02 = self.code_loader.get_qualifier_values("INS02")
        valid_ins03 = self.code_loader.get_qualifier_values("INS03")
        valid_ins04 = self.code_loader.get_qualifier_values("INS04")
        
        for segment in ins_segments:
            ins01 = None
            ins02 = None
            ins03 = None
            ins04 = None
            
            if "elements" in segment:
                for element in segment["elements"]:
                    pos = element.get("position")
                    if pos == "01":
                        ins01 = element.get("value")
                    elif pos == "02":
                        ins02 = element.get("value")
                    elif pos == "03":
                        ins03 = element.get("value")
                    elif pos == "04":
                        ins04 = element.get("value")
            
            # INS01 - Member Indicator
            if ins01 and ins01 not in valid_ins01:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.ERROR,
                        segment="INS",
                        field="INS01",
                        error=f"Invalid member indicator: {ins01}",
                        suggestion=f"Use valid value: {', '.join(sorted(valid_ins01))}",
                        fixable=False,
                        value=ins01,
                        code="834001"
                    )
                )
            
            # INS02 - Relationship Code
            if ins02 and ins02 not in valid_ins02:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.ERROR,
                        segment="INS",
                        field="INS02",
                        error=f"Invalid relationship code: {ins02}",
                        suggestion=f"Use valid relationship code (e.g., 18=Self, 01=Spouse)",
                        fixable=False,
                        value=ins02,
                        code="834002"
                    )
                )
            
            # INS03 - Maintenance Type Code
            if ins03 and ins03 not in valid_ins03:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.ERROR,
                        segment="INS",
                        field="INS03",
                        error=f"Invalid maintenance type code: {ins03}",
                        suggestion=f"Use valid code (e.g., 021=Addition, 001=Change, 024=Termination)",
                        fixable=False,
                        value=ins03,
                        code="834005"
                    )
                )
            
            # INS04 - Maintenance Reason Code
            if ins04 and ins04 not in valid_ins04:
                self.errors.append(
                    ValidationError(
                        layer=ErrorLayer.BUSINESS,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.ERROR,
                        segment="INS",
                        field="INS04",
                        error=f"Invalid maintenance reason code: {ins04}",
                        suggestion=f"Use valid reason code (e.g., XN=Non-Payment, 28=Initial Enrollment)",
                        fixable=False,
                        value=ins04,
                        code="834006"
                    )
                )
        
        # Duplicate member detection
        self._check_duplicate_members(context)
