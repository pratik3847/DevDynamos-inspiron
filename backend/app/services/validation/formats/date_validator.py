"""
Date Format Validator
Validates EDI date formats (CCYYMMDD, CCYYMM, etc.)
"""
import re
from datetime import datetime
from typing import Optional, Tuple


class DateValidator:
    """Validates EDI date formats"""
    
    # Common EDI date formats
    FORMATS = {
        "CCYYMMDD": r'^\d{8}$',  # 20240101
        "CCYYMM": r'^\d{6}$',    # 202401
        "CCYY": r'^\d{4}$',      # 2024
    }
    
    @staticmethod
    def is_valid_format(date_str: str, format_type: str = "CCYYMMDD") -> bool:
        """Check if date matches expected format"""
        if not date_str:
            return False
        pattern = DateValidator.FORMATS.get(format_type)
        if not pattern:
            return False
        return bool(re.match(pattern, date_str))
    
    @staticmethod
    def parse_date(date_str: str, format_type: str = "CCYYMMDD") -> Optional[datetime]:
        """Parse EDI date string to datetime object"""
        if not date_str:
            return None
        
        try:
            if format_type == "CCYYMMDD" and len(date_str) == 8:
                return datetime.strptime(date_str, "%Y%m%d")
            elif format_type == "CCYYMM" and len(date_str) == 6:
                return datetime.strptime(date_str, "%Y%m")
            elif format_type == "CCYY" and len(date_str) == 4:
                return datetime.strptime(date_str, "%Y")
        except ValueError:
            return None
        
        return None
    
    @staticmethod
    def is_valid_date(date_str: str, format_type: str = "CCYYMMDD") -> bool:
        """Check if date is valid (format + parseable)"""
        if not DateValidator.is_valid_format(date_str, format_type):
            return False
        return DateValidator.parse_date(date_str, format_type) is not None
    
    @staticmethod
    def is_future_date(date_str: str, format_type: str = "CCYYMMDD") -> bool:
        """Check if date is in the future"""
        parsed = DateValidator.parse_date(date_str, format_type)
        if not parsed:
            return False
        return parsed > datetime.now()
    
    @staticmethod
    def is_reasonable_dob(date_str: str) -> bool:
        """Check if date is reasonable for date of birth (not future, not too old)"""
        parsed = DateValidator.parse_date(date_str, "CCYYMMDD")
        if not parsed:
            return False
        
        now = datetime.now()
        age = (now - parsed).days / 365.25
        
        # Reasonable age range: 0-120 years
        return 0 <= age <= 120
    
    @staticmethod
    def compare_dates(date1: str, date2: str, format_type: str = "CCYYMMDD") -> Optional[int]:
        """
        Compare two dates
        Returns: -1 if date1 < date2, 0 if equal, 1 if date1 > date2, None if invalid
        """
        parsed1 = DateValidator.parse_date(date1, format_type)
        parsed2 = DateValidator.parse_date(date2, format_type)
        
        if not parsed1 or not parsed2:
            return None
        
        if parsed1 < parsed2:
            return -1
        elif parsed1 > parsed2:
            return 1
        return 0
    
    @staticmethod
    def validate(date_str: str, format_type: str = "CCYYMMDD", 
                 allow_future: bool = True, check_dob: bool = False) -> Tuple[bool, str]:
        """
        Comprehensive date validation
        Returns: (is_valid, error_message)
        """
        if not date_str:
            return False, "Date is required"
        
        if not DateValidator.is_valid_format(date_str, format_type):
            return False, f"Date must be in {format_type} format"
        
        if not DateValidator.is_valid_date(date_str, format_type):
            return False, "Invalid date value"
        
        if not allow_future and DateValidator.is_future_date(date_str, format_type):
            return False, "Date cannot be in the future"
        
        if check_dob and not DateValidator.is_reasonable_dob(date_str):
            return False, "Date of birth is not reasonable (must be 0-120 years old)"
        
        return True, ""
    
    @staticmethod
    def get_suggestion(date_str: str, format_type: str = "CCYYMMDD") -> str:
        """Get suggestion for invalid date"""
        if not date_str:
            return f"Provide date in {format_type} format"
        if not DateValidator.is_valid_format(date_str, format_type):
            return f"Format date as {format_type} (e.g., 20240101 for Jan 1, 2024)"
        return "Ensure date is valid (check month/day values)"
