"""
External Validator - Layer 3
Validates data against external APIs (async, non-blocking)
"""
import asyncio
from typing import List
from ..models import ValidationError, ValidationContext, ErrorSeverity, ErrorLayer, ErrorType
from ..external import get_nppes_client


class ExternalValidator:
    """Layer 3: Validates against external data sources (async)"""
    
    def __init__(self, enable_external: bool = True):
        self.enable_external = enable_external
        self.warnings: List[ValidationError] = []
        self.nppes_client = get_nppes_client() if enable_external else None
    
    def validate_sync(self, context: ValidationContext) -> List[ValidationError]:
        """
        Synchronous external validation
        Returns warnings only (never blocks validation)
        """
        if not self.enable_external or not self.nppes_client:
            return []
        
        self.warnings = []
        
        try:
            # Validate NPIs against NPPES
            self._validate_npis_sync(context)
        except Exception as e:
            # External validation failures should not block
            self.warnings.append(
                ValidationError(
                    layer=ErrorLayer.EXTERNAL,
                    type=ErrorType.CODE,
                    severity=ErrorSeverity.WARNING,
                    segment="EXTERNAL",
                    error=f"External validation unavailable: {str(e)}",
                    suggestion="External validation will be skipped"
                )
            )
        
        return self.warnings
    
    def _validate_npis_sync(self, context: ValidationContext):
        """Validate NPIs against NPPES registry (synchronous)"""
        # Collect all NPIs from NM1 segments with XX qualifier
        npis_to_validate = []
        
        nm1_segments = context.get_all_segments("NM1")
        
        for segment in nm1_segments:
            qualifier = None
            npi = None
            
            if "elements" in segment:
                for element in segment["elements"]:
                    pos = element.get("position")
                    if pos == "08":
                        qualifier = element.get("value")
                    elif pos == "09":
                        npi = element.get("value")
            
            if qualifier == "XX" and npi:
                npis_to_validate.append(npi)

        # De-duplicate to avoid repeated external calls
        npis_to_validate = list(dict.fromkeys(npis_to_validate))
        
        # Validate each NPI
        for npi in npis_to_validate:
            result = self.nppes_client.validate_npi(npi)
            
            if result.get("error"):
                # API error - add warning
                self.warnings.append(
                    ValidationError(
                        layer=ErrorLayer.EXTERNAL,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.WARNING,
                        segment="NM1",
                        field="NM109",
                        error=f"NPI {npi}: {result['error']}",
                        suggestion="Verify NPI manually at https://npiregistry.cms.hhs.gov",
                        value=npi,
                        code="NPPES001"
                    )
                )
            elif not result.get("valid"):
                # NPI not valid
                status = result.get("status", "Unknown")
                self.warnings.append(
                    ValidationError(
                        layer=ErrorLayer.EXTERNAL,
                        type=ErrorType.CODE,
                        severity=ErrorSeverity.WARNING,
                        segment="NM1",
                        field="NM109",
                        error=f"NPI {npi} is not active in NPPES registry (Status: {status})",
                        suggestion="Verify NPI is correct and active",
                        value=npi,
                        code="NPPES002"
                    )
                )
            else:
                # NPI is valid - could add info message
                provider_type = result.get("type", "Unknown")
                provider_name = result.get("name", "Unknown")
                # Optionally log successful validation
                pass
    
    def validate_async(self, context: ValidationContext) -> List[ValidationError]:
        """
        Execute external validations asynchronously
        Returns warnings only (never blocks validation)
        """
        if not self.enable_external:
            return []
        
        self.warnings = []
        
        try:
            # Run async validations
            asyncio.create_task(self._validate_npis_async(context))
        except Exception as e:
            # External validation failures should not block
            self.warnings.append(
                ValidationError(
                    layer=ErrorLayer.EXTERNAL,
                    type=ErrorType.CODE,
                    severity=ErrorSeverity.WARNING,
                    segment="EXTERNAL",
                    error=f"External validation unavailable: {str(e)}",
                    suggestion="External validation will be skipped"
                )
            )
        
        return self.warnings
    
    async def _validate_npis_async(self, context: ValidationContext):
        """
        Validate NPIs against NPPES registry (async)
        This is a placeholder for async implementation
        """
        # For now, use sync version
        # In production, implement true async with aiohttp
        pass
