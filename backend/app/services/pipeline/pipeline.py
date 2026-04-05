from app.database import sessions_collection
from app.models.session_model import create_session
from app.services.agents.validator_agent import ValidatorAgent
from app.services.agents.fix_agent import FixAgent
from app.services.validation.validator import ValidationConfig
from app.services.enrollment import build_834_member_enrollment_summary
import datetime

# Import the new pyx12 robust parser
from app.services.parser.parser import parser_agent

# Import 835 remittance parser
from app.services.parser_835.parser_835 import Parser835

# Validation configuration
# External validation enables calls to external data sources (e.g., NPPES) and is collected as warnings.
validator_config = ValidationConfig(enable_external_validation=True)
validator_instance = ValidatorAgent(config=validator_config)
fix_instance = FixAgent()


def _detect_transaction_type(edi_data: dict, default: str = "837P") -> str:
    """Best-effort transaction type detection from parsed EDI data.

    Uses ST01 (Transaction Set Identifier Code). Maps 837 -> 837P by default.
    """
    if not isinstance(edi_data, dict):
        return default

    segments = edi_data.get("segments") or []
    if not isinstance(segments, list):
        return default

    st01 = None
    for seg in segments:
        if seg.get("segmentId") != "ST":
            continue
        for el in seg.get("elements", []) or []:
            if el.get("position") == "01":
                st01 = el.get("value")
                break
        break

    if not st01:
        return default

    st01 = str(st01).strip()
    if st01 == "837":
        return "837P"
    if st01 in ("835", "834"):
        return st01
    return st01 or default


def _normalize_validation_errors(errors: list) -> list:
    """Ensure validation errors have stable keys for downstream agents/UI."""
    normalized = []
    for idx, err in enumerate(errors or []):
        if not isinstance(err, dict):
            continue

        segment = err.get("segment")
        field = err.get("field") or err.get("element")
        code = err.get("code")
        line_number = err.get("line_number")
        raw_error = err.get("error")

        stable_id = err.get("id")
        if not stable_id:
            parts = [
                p for p in [segment, field, code, str(line_number) if line_number is not None else None]
                if p
            ]
            base = "_".join(parts) if parts else "ERR"
            stable_id = f"{base}_{idx}"

        normalized.append({
            **err,
            "id": stable_id,
            # Aliases used by the frontend mapper and fix agent
            "element": err.get("element") or field,
            "description": err.get("description") or raw_error,
            "lineNumber": err.get("lineNumber") or line_number,
        })

    return normalized


def validator_agent(edi_data: dict, transaction_type: str = "837P") -> list:
    """Shared validator entrypoint used by both the upload pipeline and fix-apply."""
    if not transaction_type or transaction_type == "auto":
        transaction_type = _detect_transaction_type(edi_data, default="837P")
    result_obj = validator_instance.validate_sync(edi_data, transaction_type=transaction_type)
    result = result_obj.to_dict()
    errors = _normalize_validation_errors(result.get("errors", []))
    warnings = _normalize_validation_errors(result.get("warnings", []))
    return errors + warnings

def fix_agent(validation_result: dict, parsed: dict) -> list:
    """
    Simulates the AI Fix Agent. Examines validation errors and produces suggestions.
    """
    return fix_instance.generate_fixes(validation_result, parsed)

async def run_pipeline(edi_text: str, userId: str, file_name: str) -> dict:
    """
    Central controller for the system.
    Orchestrates the workflow: Parser -> Validator -> Fixer -> Database Persistence.
    """
    
    # 1. Call REAL Pyx12 parser agent 
    parsed = parser_agent(edi_text)

    transaction_type = _detect_transaction_type(parsed, default="837P")
    
    # 1.5 For 835 files, also run specialized 835 parser
    parsed_835_data = None
    if transaction_type == "835":
        try:
            parser_835 = Parser835()
            parsed_835_data = parser_835.parse_file(edi_text)
            # Add enriched patient names to claims
            for claim in parsed_835_data.get("claims", []):
                patient = claim.get("patient", {})
                claim["patient_name"] = f"{patient.get('last_name', '')}, {patient.get('first_name', '')}".strip(", ")
        except Exception as e:
            print(f"835 parser error: {e}")
            # Continue with standard parsing even if 835 parser fails
    
    # 2. Call REAL validator agent
    # Using validate_sync to stay within synchronous flow for now, but ValidatorAgent supports async execute()
    val_result_obj = validator_instance.validate_sync(parsed, transaction_type=transaction_type)
    val_result = val_result_obj.to_dict()

    # Normalize errors + warnings for consistent downstream use
    errors = _normalize_validation_errors(val_result.get("errors", []))
    warnings = _normalize_validation_errors(val_result.get("warnings", []))
    val_result["errors"] = errors
    val_result["warnings"] = warnings

    # Persist both errors and warnings to the session so the UI can render them.
    issues = errors + warnings
    
    # 3. Call fix agent
    fixes = fix_agent(val_result, parsed)

    # 3.1 Build centralized member enrollment summary for Dashboard 835/834 view.
    member_summary = build_834_member_enrollment_summary(parsed)
    
    # 4. Create and persist session in MongoDB
    session_doc = create_session(
        userId=userId,
        fileName=file_name,
        edi_text=edi_text,
        parsed=parsed,
        errors=issues,
        fixes=fixes,
        member_enrollment_summary=member_summary,
    )
    
    # 4.1 Add 835-specific parsed data if available
    if parsed_835_data:
        session_doc["parsed_835"] = parsed_835_data
    
    # Insert safely
    if sessions_collection is None:
        raise RuntimeError("Database connection not configured")

    result = sessions_collection.insert_one(session_doc)
    session_id = str(result.inserted_id)
    
    # 5. Prepare and return response object
    return {
        "sessionId": session_id,
        "status": "Success"
    }
