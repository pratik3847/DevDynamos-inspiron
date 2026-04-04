"""
Reference Data Loader
Loads and caches code sets for validation
"""
import json
import os
from typing import Dict, Any, Optional, Set
from pathlib import Path


class CodeSetLoader:
    """Loads and manages reference data code sets"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent / "code_sets"
        self._cache: Dict[str, Any] = {}
        self._loaded = False
    
    def load_all(self):
        """Load all code sets into memory"""
        if self._loaded:
            return
        
        self._cache["qualifiers"] = self._load_json("qualifiers.json")
        self._cache["carc"] = self._load_json("carc_codes.json")
        self._cache["place_of_service"] = self._load_json("place_of_service.json")
        self._cache["icd10"] = self._load_json("icd10_sample.json")
        self._cache["hcpcs"] = self._load_json("hcpcs_sample.json")
        
        self._loaded = True
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON file from code_sets directory"""
        file_path = self.base_path / filename
        
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return {}
    
    def get_qualifier_values(self, qualifier_code: str) -> Set[str]:
        """
        Get valid values for a qualifier code
        
        Args:
            qualifier_code: Qualifier code (e.g., "NM108", "INS01")
        
        Returns:
            Set of valid values
        """
        if not self._loaded:
            self.load_all()
        
        qualifiers = self._cache.get("qualifiers", {})
        qualifier_data = qualifiers.get(qualifier_code, {})
        values = qualifier_data.get("values", {})
        
        return set(values.keys())
    
    def is_valid_qualifier_value(self, qualifier_code: str, value: str) -> bool:
        """
        Check if a value is valid for a qualifier
        
        Args:
            qualifier_code: Qualifier code (e.g., "NM108")
            value: Value to check
        
        Returns:
            True if valid, False otherwise
        """
        valid_values = self.get_qualifier_values(qualifier_code)
        return value in valid_values
    
    def get_qualifier_description(self, qualifier_code: str, value: str) -> Optional[str]:
        """
        Get description for a qualifier value
        
        Args:
            qualifier_code: Qualifier code
            value: Value
        
        Returns:
            Description or None
        """
        if not self._loaded:
            self.load_all()
        
        qualifiers = self._cache.get("qualifiers", {})
        qualifier_data = qualifiers.get(qualifier_code, {})
        values = qualifier_data.get("values", {})
        
        return values.get(value)
    
    def is_valid_carc(self, code: str) -> bool:
        """
        Check if CARC code is valid
        
        Args:
            code: CARC code
        
        Returns:
            True if valid
        """
        if not self._loaded:
            self.load_all()
        
        carc_data = self._cache.get("carc", {})
        codes = carc_data.get("codes", {})
        
        return code in codes
    
    def get_carc_description(self, code: str) -> Optional[str]:
        """Get CARC code description"""
        if not self._loaded:
            self.load_all()
        
        carc_data = self._cache.get("carc", {})
        codes = carc_data.get("codes", {})
        
        return codes.get(code)
    
    def is_valid_place_of_service(self, code: str) -> bool:
        """Check if Place of Service code is valid"""
        if not self._loaded:
            self.load_all()
        
        pos_data = self._cache.get("place_of_service", {})
        codes = pos_data.get("codes", {})
        
        return code in codes
    
    def get_place_of_service_description(self, code: str) -> Optional[str]:
        """Get Place of Service description"""
        if not self._loaded:
            self.load_all()
        
        pos_data = self._cache.get("place_of_service", {})
        codes = pos_data.get("codes", {})
        
        return codes.get(code)
    
    def get_all_qualifiers(self) -> Dict[str, Any]:
        """Get all qualifier definitions"""
        if not self._loaded:
            self.load_all()
        
        return self._cache.get("qualifiers", {})
    
    def is_valid_icd10(self, code: str) -> bool:
        """
        Check if ICD-10 code is valid
        
        Args:
            code: ICD-10 code (e.g., "E11.9", "I10")
        
        Returns:
            True if valid
        """
        if not self._loaded:
            self.load_all()
        
        icd10_data = self._cache.get("icd10", {})
        codes = icd10_data.get("codes", {})
        
        return code in codes
    
    def get_icd10_description(self, code: str) -> Optional[str]:
        """Get ICD-10 code description"""
        if not self._loaded:
            self.load_all()
        
        icd10_data = self._cache.get("icd10", {})
        codes = icd10_data.get("codes", {})
        
        return codes.get(code)
    
    def get_icd10_category(self, code: str) -> Optional[str]:
        """Get ICD-10 category for a code"""
        if not self._loaded:
            self.load_all()
        
        icd10_data = self._cache.get("icd10", {})
        categories = icd10_data.get("categories", {})
        
        # Determine category based on first character
        if not code:
            return None
        
        first_char = code[0].upper()
        
        # Find matching category range
        for range_key, description in categories.items():
            start = range_key.split('-')[0][0]
            end = range_key.split('-')[1][0]
            
            if start <= first_char <= end:
                return description
        
        return None
    
    def is_valid_hcpcs(self, code: str) -> bool:
        """
        Check if HCPCS code is valid
        
        Args:
            code: HCPCS code (e.g., "A0428", "J1200")
        
        Returns:
            True if valid
        """
        if not self._loaded:
            self.load_all()
        
        hcpcs_data = self._cache.get("hcpcs", {})
        codes = hcpcs_data.get("codes", {})
        
        return code in codes
    
    def get_hcpcs_description(self, code: str) -> Optional[str]:
        """Get HCPCS code description"""
        if not self._loaded:
            self.load_all()
        
        hcpcs_data = self._cache.get("hcpcs", {})
        codes = hcpcs_data.get("codes", {})
        
        return codes.get(code)
    
    def get_hcpcs_category(self, code: str) -> Optional[str]:
        """Get HCPCS category for a code"""
        if not self._loaded:
            self.load_all()
        
        hcpcs_data = self._cache.get("hcpcs", {})
        categories = hcpcs_data.get("categories", {})
        
        if not code:
            return None
        
        # HCPCS categories are based on first letter
        first_letter = code[0].upper()
        
        return categories.get(first_letter)
    
    def get_code_set_stats(self) -> Dict[str, int]:
        """Get statistics about loaded code sets"""
        if not self._loaded:
            self.load_all()
        
        stats = {}
        
        # Count qualifiers
        qualifiers = self._cache.get("qualifiers", {})
        stats["qualifiers"] = len(qualifiers)
        
        # Count CARC codes
        carc = self._cache.get("carc", {})
        stats["carc_codes"] = len(carc.get("codes", {}))
        
        # Count Place of Service
        pos = self._cache.get("place_of_service", {})
        stats["place_of_service"] = len(pos.get("codes", {}))
        
        # Count ICD-10
        icd10 = self._cache.get("icd10", {})
        stats["icd10_codes"] = len(icd10.get("codes", {}))
        
        # Count HCPCS
        hcpcs = self._cache.get("hcpcs", {})
        stats["hcpcs_codes"] = len(hcpcs.get("codes", {}))
        
        return stats


# Global singleton instance
_code_set_loader = None


def get_code_set_loader() -> CodeSetLoader:
    """Get singleton instance of CodeSetLoader"""
    global _code_set_loader
    
    if _code_set_loader is None:
        _code_set_loader = CodeSetLoader()
        _code_set_loader.load_all()
    
    return _code_set_loader
