"""
NPI (National Provider Identifier) Validator
Validates 10-digit NPI with Luhn checksum algorithm
"""
import re


class NPIValidator:
    """Validates NPI format and checksum"""
    
    @staticmethod
    def is_valid_format(npi: str) -> bool:
        """Check if NPI has valid format (10 digits)"""
        if not npi:
            return False
        return bool(re.match(r'^\d{10}$', npi))
    
    @staticmethod
    def luhn_check(npi: str) -> bool:
        """
        Validate NPI using Luhn algorithm (mod 10)
        NPI uses Luhn algorithm with prefix 80840
        """
        if not npi or len(npi) != 10:
            return False
        
        # Add prefix 80840 as per NPI specification
        full_number = "80840" + npi
        
        # Luhn algorithm
        total = 0
        for i, digit in enumerate(reversed(full_number)):
            n = int(digit)
            if i % 2 == 0:  # Even position (from right, 0-indexed)
                total += n
            else:  # Odd position - double it
                doubled = n * 2
                total += doubled if doubled < 10 else doubled - 9
        
        return total % 10 == 0
    
    @staticmethod
    def validate(npi: str) -> tuple[bool, str]:
        """
        Validate NPI completely
        Returns: (is_valid, error_message)
        """
        if not npi:
            return False, "NPI is required"
        
        if not NPIValidator.is_valid_format(npi):
            return False, "NPI must be exactly 10 digits"
        
        if not NPIValidator.luhn_check(npi):
            return False, "NPI failed Luhn checksum validation"
        
        return True, ""
    
    @staticmethod
    def get_suggestion(npi: str) -> str:
        """Get suggestion for invalid NPI"""
        if not npi:
            return "Provide a valid 10-digit NPI"
        if len(npi) != 10:
            return f"NPI must be 10 digits (current: {len(npi)} digits)"
        if not npi.isdigit():
            return "NPI must contain only numeric digits"
        return "Verify NPI against NPPES registry at https://npiregistry.cms.hhs.gov"
