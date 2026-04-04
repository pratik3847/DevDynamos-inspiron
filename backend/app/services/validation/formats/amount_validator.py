"""
Monetary Amount Validator
Validates monetary amounts in EDI format
"""
import re
from decimal import Decimal, InvalidOperation
from typing import Tuple


class AmountValidator:
    """Validates monetary amounts"""
    
    # EDI amount format: up to 18 digits with 2 decimal places
    AMOUNT_PATTERN = re.compile(r'^\d{1,16}(\.\d{1,2})?$')
    
    @staticmethod
    def is_valid_format(amount: str) -> bool:
        """Check if amount has valid format"""
        if not amount:
            return False
        return bool(AmountValidator.AMOUNT_PATTERN.match(amount))
    
    @staticmethod
    def parse_amount(amount: str) -> Decimal:
        """Parse amount string to Decimal"""
        try:
            return Decimal(amount)
        except (InvalidOperation, ValueError):
            return None
    
    @staticmethod
    def is_positive(amount: str) -> bool:
        """Check if amount is positive"""
        parsed = AmountValidator.parse_amount(amount)
        return parsed is not None and parsed > 0
    
    @staticmethod
    def is_non_negative(amount: str) -> bool:
        """Check if amount is non-negative"""
        parsed = AmountValidator.parse_amount(amount)
        return parsed is not None and parsed >= 0
    
    @staticmethod
    def has_valid_precision(amount: str, max_decimals: int = 2) -> bool:
        """Check if amount has valid decimal precision"""
        if '.' not in amount:
            return True
        decimal_part = amount.split('.')[1]
        return len(decimal_part) <= max_decimals
    
    @staticmethod
    def is_within_range(amount: str, min_val: float = 0, max_val: float = 999999999.99) -> bool:
        """Check if amount is within reasonable range"""
        parsed = AmountValidator.parse_amount(amount)
        if parsed is None:
            return False
        return Decimal(str(min_val)) <= parsed <= Decimal(str(max_val))
    
    @staticmethod
    def validate(amount: str, allow_negative: bool = False, 
                 allow_zero: bool = True, max_decimals: int = 2) -> Tuple[bool, str]:
        """
        Comprehensive amount validation
        Returns: (is_valid, error_message)
        """
        if not amount:
            return False, "Amount is required"
        
        if not AmountValidator.is_valid_format(amount):
            return False, "Invalid amount format (must be numeric with up to 2 decimal places)"
        
        parsed = AmountValidator.parse_amount(amount)
        if parsed is None:
            return False, "Cannot parse amount value"
        
        if not allow_negative and parsed < 0:
            return False, "Amount cannot be negative"
        
        if not allow_zero and parsed == 0:
            return False, "Amount cannot be zero"
        
        if not AmountValidator.has_valid_precision(amount, max_decimals):
            return False, f"Amount cannot have more than {max_decimals} decimal places"
        
        if not AmountValidator.is_within_range(amount):
            return False, "Amount is outside valid range"
        
        return True, ""
    
    @staticmethod
    def compare_amounts(amount1: str, amount2: str, tolerance: float = 0.01) -> bool:
        """
        Compare two amounts with tolerance
        Returns True if amounts are equal within tolerance
        """
        parsed1 = AmountValidator.parse_amount(amount1)
        parsed2 = AmountValidator.parse_amount(amount2)
        
        if parsed1 is None or parsed2 is None:
            return False
        
        diff = abs(parsed1 - parsed2)
        return diff <= Decimal(str(tolerance))
    
    @staticmethod
    def sum_amounts(amounts: list) -> Decimal:
        """Sum a list of amount strings"""
        total = Decimal('0')
        for amount in amounts:
            parsed = AmountValidator.parse_amount(amount)
            if parsed:
                total += parsed
        return total
    
    @staticmethod
    def get_suggestion(amount: str) -> str:
        """Get suggestion for invalid amount"""
        if not amount:
            return "Provide a valid monetary amount"
        if not amount.replace('.', '').replace('-', '').isdigit():
            return "Amount must contain only digits and optional decimal point"
        return "Ensure amount has valid format (e.g., 100.00, 1234.56)"
