"""
Example Usage of EDI Validation Engine
Demonstrates how to use the validator
"""
from .validator import EDIValidator, ValidationConfig, ValidatorFactory


def example_basic_validation():
    """Basic validation example"""
    
    # Sample parsed EDI data (simplified structure)
    edi_data = {
        "segments": [
            {"id": "ISA", "ISA13": "000000001"},
            {"id": "GS", "GS06": "1"},
            {"id": "ST", "ST01": "837", "ST02": "0001"},
            {"id": "BHT", "BHT01": "0019"},
            {
                "id": "NM1",
                "NM101": "IL",
                "NM108": "XX",
                "NM109": "1234567893"  # Valid NPI with Luhn check
            },
            {
                "id": "DMG",
                "DMG02": "19850615"  # DOB
            },
            {
                "id": "CLM",
                "CLM01": "CLAIM001",
                "CLM02": "100.00"  # Claim amount
            },
            {
                "id": "DTP",
                "DTP01": "434",  # Service date
                "DTP02": "D8",
                "DTP03": "20240101"
            },
            {"id": "SE", "SE01": "8", "SE02": "0001"},
            {"id": "GE", "GE01": "1", "GE02": "1"},
            {"id": "IEA", "IEA01": "1", "IEA02": "000000001"}
        ]
    }
    
    # Create validator
    validator = EDIValidator()
    
    # Run validation
    result = validator.validate(edi_data, transaction_type="837P")
    
    # Print results
    print(f"Status: {result.status}")
    print(f"Total Errors: {result.total_errors}")
    print(f"Total Warnings: {result.total_warnings}")
    print(f"Fixable Errors: {result.fixable_errors}")
    print(f"Processing Time: {result.processing_time:.2f}s")
    
    # Print errors
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  [{error.severity}] {error.segment}.{error.field}: {error.error}")
            if error.suggestion:
                print(f"    Suggestion: {error.suggestion}")
    
    # Get result as dict (for API response)
    result_dict = result.to_dict()
    return result_dict


def example_quick_validation():
    """Quick validation (skip external APIs)"""
    
    edi_data = {"segments": []}  # Your EDI data
    
    # Use factory to create quick validator
    validator = ValidatorFactory.create_quick_validator()
    
    result = validator.validate(edi_data, "837P")
    return result


def example_strict_validation():
    """Strict validation (warnings treated as errors)"""
    
    edi_data = {"segments": []}  # Your EDI data
    
    # Use factory to create strict validator
    validator = ValidatorFactory.create_strict_validator()
    
    result = validator.validate(edi_data, "837P")
    return result


def example_custom_config():
    """Custom validation configuration"""
    
    edi_data = {"segments": []}  # Your EDI data
    
    # Create custom configuration
    config = ValidationConfig(
        enable_external_validation=False,
        max_errors_per_file=500,
        strict_mode=False
    )
    
    validator = EDIValidator(config)
    result = validator.validate(edi_data, "837P")
    return result


def example_with_agent():
    """Using validator through agent"""
    from ..agents.validator_agent import ValidatorAgent
    
    # Create agent
    agent = ValidatorAgent()
    
    # Session state with parsed EDI
    session_state = {
        "parsed_edi": {"segments": []},
        "transaction_type": "837P"
    }
    
    # Execute validation (async)
    # result = await agent.execute(session_state)
    
    # Or use sync validation
    result = agent.validate_sync(
        edi_data={"segments": []},
        transaction_type="837P"
    )
    
    return result


if __name__ == "__main__":
    # Run basic example
    result = example_basic_validation()
    print("\n" + "="*50)
    print("Validation Complete!")
    print("="*50)
