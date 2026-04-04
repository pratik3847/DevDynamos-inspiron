"""
Code Format Validators
Validates various code formats (ZIP, phone, CPT, HCPCS, etc.)
"""
import re
from typing import Tuple


class ZIPCodeValidator:
    """Validates ZIP code formats"""
    
    ZIP5_PATTERN = re.compile(r'^\d{5}$')
    ZIP9_PATTERN = re.compile(r'^\d{5}-?\d{4}$')
    
    @staticmethod
    def is_valid_zip5(zip_code: str) -> bool:
        """Validate 5-digit ZIP code"""
        return bool(ZIPCodeValidator.ZIP5_PATTERN.match(zip_code))
    
    @staticmethod
    def is_valid_zip9(zip_code: str) -> bool:
        """Validate 9-digit ZIP code (with or without hyphen)"""
        return bool(ZIPCodeValidator.ZIP9_PATTERN.match(zip_code))
    
    @staticmethod
    def validate(zip_code: str) -> Tuple[bool, str]:
        """Validate ZIP code (5 or 9 digit)"""
        if not zip_code:
            return False, "ZIP code is required"
        
        if ZIPCodeValidator.is_valid_zip5(zip_code) or ZIPCodeValidator.is_valid_zip9(zip_code):
            return True, ""
        
        return False, "ZIP code must be 5 digits or 9 digits (XXXXX or XXXXX-XXXX)"
    
    @staticmethod
    def normalize(zip_code: str) -> str:
        """Normalize ZIP code to 9-digit format with hyphen"""
        if not zip_code:
            return zip_code
        
        # Remove existing hyphens
        clean = zip_code.replace('-', '')
        
        if len(clean) == 5:
            return clean
        elif len(clean) == 9:
            return f"{clean[:5]}-{clean[5:]}"
        
        return zip_code


class PhoneValidator:
    """Validates phone number formats"""
    
    PHONE_PATTERN = re.compile(r'^\d{10}$')
    
    @staticmethod
    def validate(phone: str) -> Tuple[bool, str]:
        """Validate 10-digit phone number"""
        if not phone:
            return False, "Phone number is required"
        
        # Remove common separators
        clean = phone.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        
        if PhoneValidator.PHONE_PATTERN.match(clean):
            return True, ""
        
        return False, "Phone number must be 10 digits"


class CPTCodeValidator:
    """Validates CPT (Current Procedural Terminology) codes"""
    
    CPT_PATTERN = re.compile(r'^\d{5}$')
    
    @staticmethod
    def is_valid_format(code: str) -> bool:
        """Check if CPT code has valid format (5 digits)"""
        return bool(CPTCodeValidator.CPT_PATTERN.match(code))
    
    @staticmethod
    def validate(code: str) -> Tuple[bool, str]:
        """Validate CPT code format"""
        if not code:
            return False, "CPT code is required"
        
        if CPTCodeValidator.is_valid_format(code):
            return True, ""
        
        return False, "CPT code must be exactly 5 digits"


class HCPCSCodeValidator:
    """Validates HCPCS (Healthcare Common Procedure Coding System) codes"""
    
    # HCPCS: 1 letter + 4 digits (e.g., A0428, J1234)
    HCPCS_PATTERN = re.compile(r'^[A-Z]\d{4}$')
    
    @staticmethod
    def is_valid_format(code: str) -> bool:
        """Check if HCPCS code has valid format"""
        return bool(HCPCSCodeValidator.HCPCS_PATTERN.match(code))
    
    @staticmethod
    def validate(code: str) -> Tuple[bool, str]:
        """Validate HCPCS code format"""
        if not code:
            return False, "HCPCS code is required"
        
        if HCPCSCodeValidator.is_valid_format(code):
            return True, ""
        
        return False, "HCPCS code must be 1 letter followed by 4 digits (e.g., A0428)"


class ProcedureCodeValidator:
    """Validates procedure codes (CPT or HCPCS)"""
    
    @staticmethod
    def validate(code: str, code_type: str = None) -> Tuple[bool, str]:
        """
        Validate procedure code
        code_type: 'CPT', 'HCPCS', or None (auto-detect)
        """
        if not code:
            return False, "Procedure code is required"
        
        # Auto-detect if not specified
        if code_type is None:
            if code.isdigit() and len(code) == 5:
                code_type = 'CPT'
            elif len(code) == 5 and code[0].isalpha():
                code_type = 'HCPCS'
            else:
                return False, "Invalid procedure code format"
        
        if code_type == 'CPT':
            return CPTCodeValidator.validate(code)
        elif code_type == 'HCPCS':
            return HCPCSCodeValidator.validate(code)
        
        return False, "Unknown code type"


class ICD10Validator:
    """Validates ICD-10 diagnosis codes"""
    
    # ICD-10: 3-7 characters, starts with letter, may contain decimal
    ICD10_PATTERN = re.compile(r'^[A-Z]\d{2}(\.\d{1,4})?$')
    
    @staticmethod
    def is_valid_format(code: str) -> bool:
        """Check if ICD-10 code has valid format"""
        return bool(ICD10Validator.ICD10_PATTERN.match(code))
    
    @staticmethod
    def validate(code: str) -> Tuple[bool, str]:
        """Validate ICD-10 code format"""
        if not code:
            return False, "ICD-10 code is required"
        
        if ICD10Validator.is_valid_format(code):
            return True, ""
        
        return False, "ICD-10 code must start with letter followed by 2 digits (e.g., A01, Z12.34)"


class TaxIDValidator:
    """Validates Tax ID (EIN) format"""
    
    EIN_PATTERN = re.compile(r'^\d{9}$')
    
    @staticmethod
    def validate(tax_id: str) -> Tuple[bool, str]:
        """Validate Tax ID (9 digits)"""
        if not tax_id:
            return False, "Tax ID is required"
        
        clean = tax_id.replace('-', '')
        
        if TaxIDValidator.EIN_PATTERN.match(clean):
            return True, ""
        
        return False, "Tax ID must be 9 digits"


class SSNValidator:
    """Validates Social Security Number format"""
    
    SSN_PATTERN = re.compile(r'^\d{9}$')
    
    @staticmethod
    def validate(ssn: str) -> Tuple[bool, str]:
        """Validate SSN (9 digits)"""
        if not ssn:
            return False, "SSN is required"
        
        clean = ssn.replace('-', '')
        
        if SSNValidator.SSN_PATTERN.match(clean):
            return True, ""
        
        return False, "SSN must be 9 digits"
