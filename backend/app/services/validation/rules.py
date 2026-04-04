"""
Validation Rules Definitions
A declarative set of rules (e.g., "SNIP level 1/2 checks") to be consumed by `validator.py`.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from .models import ValidationError, ValidationContext, ErrorSeverity, ErrorLayer, ErrorType


class ValidationRule(ABC):
    """Base class for all validation rules"""
    
    def __init__(self, code: str, severity: ErrorSeverity, message: str, layer: ErrorLayer):
        self.code = code
        self.severity = severity
        self.message = message
        self.layer = layer
    
    @abstractmethod
    def validate(self, context: ValidationContext) -> List[ValidationError]:
        """Execute validation and return list of errors"""
        pass
    
    def create_error(
        self,
        segment: str,
        error_type: ErrorType,
        error_message: str,
        field: Optional[str] = None,
        suggestion: Optional[str] = None,
        fixable: bool = False,
        loop: Optional[str] = None,
        value: Optional[str] = None
    ) -> ValidationError:
        """Helper to create validation error"""
        return ValidationError(
            layer=self.layer,
            type=error_type,
            severity=self.severity,
            segment=segment,
            field=field,
            error=error_message,
            suggestion=suggestion,
            fixable=fixable,
            loop=loop,
            value=value,
            code=self.code
        )


class RuleRegistry:
    """Registry to manage all validation rules"""
    
    def __init__(self):
        self._rules: Dict[str, List[ValidationRule]] = {
            "structural": [],
            "business": [],
            "external": []
        }
    
    def register(self, layer: str, rule: ValidationRule):
        """Register a rule to a specific layer"""
        if layer in self._rules:
            self._rules[layer].append(rule)
    
    def get_rules(self, layer: str) -> List[ValidationRule]:
        """Get all rules for a layer"""
        return self._rules.get(layer, [])
    
    def get_all_rules(self) -> List[ValidationRule]:
        """Get all registered rules"""
        all_rules = []
        for rules in self._rules.values():
            all_rules.extend(rules)
        return all_rules


# Global rule registry
rule_registry = RuleRegistry()
