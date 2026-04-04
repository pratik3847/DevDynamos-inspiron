from fastapi import APIRouter, File, UploadFile, Query, HTTPException, Depends
from fastapi.responses import Response
import json
from bson import ObjectId
from datetime import datetime
try:
    from app.database import sessions_collection
except ImportError:
    sessions_collection = None

from app.services.pipeline.pipeline import run_pipeline

try:
    from app.services.pipeline.pipeline import fix_agent as pipeline_fix_agent
except Exception:
    pipeline_fix_agent = None
from app.utils.auth import get_current_user
from app.utils.report_pdf import build_fix_report_pdf

router = APIRouter(prefix="/files", tags=["files"])


_PLACEHOLDER_VALUES = {"", "FIXED_VAL", "FIXED_VALUE", "INVALID_VAL", None}


def _is_placeholder_value(val) -> bool:
    if val is None:
        return True
    return str(val) in _PLACEHOLDER_VALUES


def _refresh_session_fixes_if_needed(session: dict) -> dict:
    """Regenerate deterministic fixes for legacy sessions.

    Old sessions may have placeholder suggested values (e.g., FIXED_VAL).
    This keeps Fix Assistant usable without forcing re-upload.
    """
    if not isinstance(session, dict) or pipeline_fix_agent is None:
        return session

    fixes = session.get("fixes") or []
    if not isinstance(fixes, list):
        fixes = []

    needs_refresh = False
    for f in fixes:
        if not isinstance(f, dict):
            continue
        if _is_placeholder_value(f.get("suggested")) or f.get("original") is None:
            needs_refresh = True
            break
        if not f.get("segmentId") or not f.get("elementId"):
            needs_refresh = True
            break

    # If fixes are empty but there are issues, generate them.
    issues = session.get("validationErrors") or []
    if (not fixes) and issues:
        needs_refresh = True

    if not needs_refresh:
        return session

    modified_json = session.get("modifiedJson") or session.get("parsedJson") or {}
    recomputed = pipeline_fix_agent({"errors": issues}, modified_json) or []

    remaining_error_ids = {str(e.get("id")) for e in issues if isinstance(e, dict) and e.get("id")}
    accepted = [
        f
        for f in fixes
        if isinstance(f, dict)
        and f.get("status") == "accepted"
        and str(f.get("errorId")) not in remaining_error_ids
    ]

    session["fixes"] = accepted + recomputed
    return session


def _backfill_original_errors_if_needed(session: dict) -> dict:
    if not isinstance(session, dict):
        return session
    if session.get("originalValidationErrors") is None:
        session["originalValidationErrors"] = session.get("validationErrors") or []
    return session

def _serialize_session(session: dict) -> dict:
    session = dict(session)
    if "_id" in session:
        session["_id"] = str(session["_id"])
    for key in ("createdAt", "updatedAt"):
        if isinstance(session.get(key), datetime):
            session[key] = session[key].isoformat()
    return session


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint for handling EDI file uploads.
    Reads the file to memory, converts it to a string, and triggers the processing pipeline.
    """
    try:
        # Read file content
        content = await file.read()
        
        # Convert to string (assuming UTF-8 encoding for standard EDI text)
        edi_text = content.decode("utf-8")
        
        if sessions_collection is None:
            raise HTTPException(status_code=503, detail="Database connection not configured")

        # Call the pipeline process logic
        result = await run_pipeline(edi_text, current_user["userId"], file.filename)
        
        return {
            "message": "File processed successfully",
            "data": result
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, 
            detail="Error decoding the file. Ensure the EDI file is encoded in UTF-8."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while handling the upload: {str(e)}"
        )

@router.get("/session/{session_id}")
async def get_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """
    Retrieve full EDI session data by its ID.
    """
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
        
    if sessions_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")
        
    session = sessions_collection.find_one({"_id": obj_id, "userId": current_user["userId"]})
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _backfill_original_errors_if_needed(session)
    session = _refresh_session_fixes_if_needed(session)
    # Persist refreshed fixes so UI/export sees real values.
    try:
        sessions_collection.update_one(
            {"_id": obj_id},
            {"$set": {"fixes": session.get("fixes", []), "originalValidationErrors": session.get("originalValidationErrors") or [], "updatedAt": datetime.utcnow()}},
        )
    except Exception:
        pass

    return _serialize_session(session)


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    if sessions_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")

    cursor = sessions_collection.find(
        {"userId": current_user["userId"]},
        {"rawEdi": 0, "modifiedJson": 0, "parsedJson": 0}
    ).sort("createdAt", -1).skip(skip).limit(limit)

    return [_serialize_session(s) for s in cursor]


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a session owned by the current user."""
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    if sessions_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")

    result = sessions_collection.delete_one({"_id": obj_id, "userId": current_user["userId"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session deleted", "sessionId": session_id}


@router.get("/session/{session_id}/download/edi")
async def download_edi(session_id: str, current_user: dict = Depends(get_current_user)):
    """Download the most current EDI payload (corrected if available, else raw)."""
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    if sessions_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")

    session = sessions_collection.find_one({"_id": obj_id, "userId": current_user["userId"]})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    filename = session.get("fileName") or "file.edi"
    base = filename.rsplit(".", 1)[0]
    out_name = f"{base}-current.edi"

    edi_text = session.get("correctedEdi") or session.get("rawEdi") or ""
    return Response(
        content=str(edi_text),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{out_name}\""},
    )


@router.get("/session/{session_id}/download/json")
async def download_json(session_id: str, current_user: dict = Depends(get_current_user)):
    """Download the current parsed/modified JSON."""
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    if sessions_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")

    session = sessions_collection.find_one({"_id": obj_id, "userId": current_user["userId"]})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    filename = session.get("fileName") or "file.edi"
    base = filename.rsplit(".", 1)[0]
    out_name = f"{base}-parsed.json"

    data = session.get("modifiedJson") or session.get("parsedJson") or {}
    body = json.dumps(data, indent=2, default=str)
    return Response(
        content=body,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{out_name}\""},
    )


@router.get("/session/{session_id}/download/report")
async def download_report(
    session_id: str,
    format: str = Query("pdf", pattern="^(pdf|json)$"),
    current_user: dict = Depends(get_current_user),
):
    """Download a detailed report of validation issues and applied fixes.

    Default is a professional PDF. Use ?format=json to get the raw JSON.
    """
    try:
        obj_id = ObjectId(session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    if sessions_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")

    session = sessions_collection.find_one({"_id": obj_id, "userId": current_user["userId"]})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _backfill_original_errors_if_needed(session)
    session = _refresh_session_fixes_if_needed(session)
    try:
        sessions_collection.update_one(
            {"_id": obj_id},
            {"$set": {"fixes": session.get("fixes", []), "originalValidationErrors": session.get("originalValidationErrors") or [], "updatedAt": datetime.utcnow()}},
        )
    except Exception:
        pass

    filename = session.get("fileName") or "file.edi"
    base = filename.rsplit(".", 1)[0]
    out_name = f"{base}-fix-report.pdf" if format == "pdf" else f"{base}-fix-report.json"

    if format == "json":
        validation_issues = session.get("validationErrors") or []
        fix_suggestions = session.get("fixes") or []
        fix_reports = session.get("fixReports") or []
        changes_log = session.get("changesLog") or []

        report = {
            "sessionId": str(session.get("_id")),
            "fileName": filename,
            "generatedAt": datetime.utcnow().isoformat(),
            "status": session.get("status"),
            "summary": {
                "currentIssueCount": len(validation_issues),
                "fixSuggestions": len(fix_suggestions),
                "fixReportEntries": len(fix_reports),
                "changesApplied": len(changes_log),
            },
            "fixSuggestions": fix_suggestions,
            "fixReports": fix_reports,
            "changesLog": changes_log,
            "currentValidationIssues": validation_issues,
        }

        body = json.dumps(report, indent=2, default=str)
        return Response(
            content=body,
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=\"{out_name}\""},
        )

    pdf_bytes = build_fix_report_pdf(session=session)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{out_name}\""},
    )
