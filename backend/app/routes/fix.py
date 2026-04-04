from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import Optional, List, Dict, Any
import copy

try:
    from app.database import sessions_collection
except ImportError:
    sessions_collection = None

try:
    from app.services.pipeline.pipeline import validator_agent
except ImportError:
    def validator_agent(parsed_data: dict):
        return []

try:
    from app.services.pipeline.pipeline import fix_agent as pipeline_fix_agent
except ImportError:
    def pipeline_fix_agent(validation_result: dict, parsed: dict) -> list:
        return []

from app.utils.auth import get_current_user

router = APIRouter(prefix="/fix", tags=["fix"])

class ApplyFixRequest(BaseModel):
    sessionId: str
    # These can be omitted if fixId is provided and can be resolved from the session.
    segmentId: Optional[str] = None
    elementId: Optional[str] = None
    newValue: Optional[str] = None
    fixId: Optional[str] = None


class ApplyFixItem(BaseModel):
    # Either provide explicit targeting, or provide fixId and let the server resolve.
    segmentId: Optional[str] = None
    elementId: Optional[str] = None
    newValue: Optional[str] = None
    fixId: Optional[str] = None


class ApplyFixBatchRequest(BaseModel):
    sessionId: str
    fixes: List[ApplyFixItem]


_PLACEHOLDER_VALUES = {"", "FIXED_VAL", "FIXED_VALUE", "INVALID_VAL", None}


def _is_placeholder_value(val: Any) -> bool:
    if val is None:
        return True
    s = str(val)
    return s in _PLACEHOLDER_VALUES


def _issue_key(err: Dict[str, Any]) -> str:
    """Stable-ish identity for comparing validation issue sets."""
    if not isinstance(err, dict):
        return ""
    if err.get("id"):
        return str(err.get("id"))
    parts = [
        err.get("segment") or "",
        err.get("field") or err.get("element") or "",
        err.get("code") or err.get("rule_id") or "",
        err.get("error") or err.get("message") or err.get("description") or "",
    ]
    return "|".join(str(p) for p in parts)


def _diff_issues(before: List[Dict[str, Any]], after: List[Dict[str, Any]]) -> Dict[str, Any]:
    before = [e for e in (before or []) if isinstance(e, dict)]
    after = [e for e in (after or []) if isinstance(e, dict)]

    before_map = {k: e for e in before if (k := _issue_key(e))}
    after_map = {k: e for e in after if (k := _issue_key(e))}

    resolved_keys = sorted(set(before_map.keys()) - set(after_map.keys()))
    introduced_keys = sorted(set(after_map.keys()) - set(before_map.keys()))
    remaining_keys = sorted(set(after_map.keys()) & set(before_map.keys()))

    return {
        "resolved": [before_map[k] for k in resolved_keys],
        "introduced": [after_map[k] for k in introduced_keys],
        "remaining": [after_map[k] for k in remaining_keys],
        "counts": {
            "before": len(before),
            "after": len(after),
            "resolved": len(resolved_keys),
            "introduced": len(introduced_keys),
            "remaining": len(remaining_keys),
        },
    }

def edi_generator(parsed: dict) -> str:
    """
    Regenerates raw EDI string from structured nested JSON.
    """
    if not isinstance(parsed, dict) or "segments" not in parsed:
        return ""
        
    result = ""
    for seg in parsed.get("segments", []):
        segment_id = seg.get("segmentId", "")
        elements = [str(el.get("value", "")) for el in seg.get("elements", [])]
        
        if elements:
            result += segment_id + "*" + "*".join(elements) + "~"
        else:
            result += segment_id + "~"
            
    return result


def _get_element_value(seg: dict, position: str) -> Optional[str]:
    if not isinstance(seg, dict):
        return None
    for el in seg.get("elements", []) or []:
        if not isinstance(el, dict):
            continue
        if str(el.get("position") or "").zfill(2) == str(position).zfill(2):
            return el.get("value")
    return None


def _set_element_value(seg: dict, position: str, value: str) -> bool:
    if not isinstance(seg, dict):
        return False
    for el in seg.get("elements", []) or []:
        if not isinstance(el, dict):
            continue
        if str(el.get("position") or "").zfill(2) == str(position).zfill(2):
            el["value"] = value
            return True
    return False


def _apply_insert_nm1_82_from_85(modified_json: dict) -> Dict[str, Any]:
    """Duplicate NM1*85 as NM1*82 inside each CLM..next CLM/SE block missing NM1*82.

    Best-effort to satisfy business validation checks.
    """
    segments = (modified_json or {}).get("segments") or []
    if not isinstance(segments, list):
        return {"inserted": 0, "reason": "modifiedJson.segments missing"}

    # Template NM1*85 (first occurrence)
    template = None
    for seg in segments:
        if not isinstance(seg, dict) or str(seg.get("segmentId") or "").upper() != "NM1":
            continue
        if _get_element_value(seg, "01") == "85":
            template = seg
            break
    if template is None:
        return {"inserted": 0, "reason": "NM1*85 not found"}

    clm_indexes = [i for i, s in enumerate(segments) if isinstance(s, dict) and s.get("segmentId") == "CLM"]
    if not clm_indexes:
        return {"inserted": 0, "reason": "No CLM segments (no claim blocks)"}

    se_index = next((i for i, s in enumerate(segments) if isinstance(s, dict) and s.get("segmentId") == "SE"), len(segments))
    inserted = 0

    # Work backwards so inserts don't shift upcoming indices.
    for idx in range(len(clm_indexes) - 1, -1, -1):
        start = clm_indexes[idx]
        end = clm_indexes[idx + 1] if idx + 1 < len(clm_indexes) else se_index
        block = segments[start:end]

        has_nm1_82 = False
        for s in block:
            if not isinstance(s, dict) or s.get("segmentId") != "NM1":
                continue
            if _get_element_value(s, "01") == "82":
                has_nm1_82 = True
                break
        if has_nm1_82:
            continue

        new_seg = copy.deepcopy(template)
        new_seg["segmentId"] = "NM1"
        _set_element_value(new_seg, "01", "82")

        insert_at = start + 1
        segments.insert(insert_at, new_seg)
        inserted += 1

    modified_json["segments"] = segments
    return {"inserted": inserted}


def _find_element_in_segment(seg: dict, element_id: str):
    """Find an element by id, or by position derived from element_id.

    Supports:
    - direct element ids (exact match)
    - raw positions like "08"
    - field-style ids like "NM108" -> "08"
    """
    if not seg or not element_id:
        return None

    elements = seg.get("elements", []) or []
    # 1) exact id match
    for el in elements:
        if str(el.get("id") or "").upper() == str(element_id).upper():
            return el

    # 2) match by position
    pos = str(element_id).strip()
    if len(pos) == 2 and pos.isdigit():
        for el in elements:
            if str(el.get("position") or "").zfill(2) == pos:
                return el

    # 3) derive pos from trailing digits (NM108 -> 08)
    digits = "".join([c for c in pos if c.isdigit()])
    if digits:
        derived = digits[-2:].zfill(2)
        for el in elements:
            if str(el.get("position") or "").zfill(2) == derived:
                return el

    return None


def _resolve_fix_target(
    session: Dict[str, Any],
    segment_id: Optional[str],
    element_id: Optional[str],
    new_value: Optional[str],
    fix_id: Optional[str],
):
    """Resolve (segmentId, elementId, newValue) from explicit fields or a stored fixId.

    Backward compatible with older sessions where fixes may not store segmentId/elementId.
    """
    # Prefer explicit targeting only when the new value is real.
    # Legacy sessions can send placeholders (or empty string) which must be ignored.
    if segment_id and element_id and new_value is not None and not _is_placeholder_value(new_value):
        return segment_id, element_id, str(new_value), None

    if not fix_id:
        raise HTTPException(status_code=400, detail="Provide segmentId/elementId/newValue or fixId")

    fixes = session.get("fixes") or []
    fix_obj = None
    for f in fixes:
        if isinstance(f, dict) and f.get("id") == fix_id:
            fix_obj = f
            break

    if not isinstance(fix_obj, dict):
        raise HTTPException(status_code=400, detail="FixId not found in session")

    seg = fix_obj.get("segmentId") or fix_obj.get("segment") or fix_obj.get("segment_id")
    el = fix_obj.get("elementId") or fix_obj.get("element") or fix_obj.get("field") or fix_obj.get("element_id")
    val = fix_obj.get("suggested") or fix_obj.get("newValue") or fix_obj.get("new_value")

    # If targeting is missing, try to derive from linked validation error
    if (not seg or not el) and fix_obj.get("errorId"):
        error_id = fix_obj.get("errorId")
        for e in session.get("validationErrors") or []:
            if isinstance(e, dict) and (e.get("id") == error_id or e.get("errorId") == error_id):
                seg = seg or e.get("segment")
                el = el or e.get("field") or e.get("element")
                break

    # If val is missing/placeholder, try recomputing from current validation issues.
    if seg and el and (val is None or _is_placeholder_value(val)):
        try:
            modified_json = session.get("modifiedJson") or session.get("parsedJson") or {}
            current_issues = session.get("validationErrors") or []
            recomputed = pipeline_fix_agent({"errors": current_issues}, modified_json) or []
            target_error_id = str(fix_obj.get("errorId") or "")
            for rf in recomputed:
                if not isinstance(rf, dict):
                    continue
                if target_error_id and str(rf.get("errorId")) != target_error_id:
                    continue
                if str(rf.get("segmentId")) != str(seg) or str(rf.get("elementId")) != str(el):
                    continue
                candidate = rf.get("suggested")
                if candidate is not None and not _is_placeholder_value(candidate):
                    return str(seg), str(el), str(candidate), fix_obj
        except Exception:
            # Fall through to generic error below.
            pass

    if seg and el and val is not None and not _is_placeholder_value(val):
        return str(seg), str(el), str(val), fix_obj

    raise HTTPException(status_code=400, detail="Unable to resolve fix target from fixId")

@router.post("/apply")
async def apply_fix(request: ApplyFixRequest, current_user: dict = Depends(get_current_user)):
    """
    Endpoint for accepting a suggested fix, updating the JSON mapping,
    logging the change, regenerating the EDI output, and persisting it to MongoDB.
    """
    # 1. Convert sessionId -> ObjectId
    try:
        obj_id = ObjectId(request.sessionId)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    if sessions_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")

    # 2. Fetch session from MongoDB
    session = sessions_collection.find_one({"_id": obj_id, "userId": current_user["userId"]})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Backfill originalValidationErrors for legacy sessions
    if session.get("originalValidationErrors") is None:
        try:
            sessions_collection.update_one(
                {"_id": obj_id},
                {"$set": {"originalValidationErrors": session.get("validationErrors") or [], "updatedAt": datetime.utcnow()}},
            )
        except Exception:
            pass

    # 3. Resolve fix object (if any) for operation handling
    fixes_list = session.get("fixes") or []
    fix_obj = None
    if request.fixId and isinstance(fixes_list, list):
        for f in fixes_list:
            if isinstance(f, dict) and f.get("id") == request.fixId:
                fix_obj = f
                break

    # 3.5 Apply non-element operations
    modified_json = session.get("modifiedJson") or {}
    if isinstance(fix_obj, dict) and str(fix_obj.get("operation") or "").upper() == "INSERT_NM1_82_FROM_85":
        before_issues = session.get("validationErrors") or []
        changes_log = session.get("changesLog") or []
        meta = _apply_insert_nm1_82_from_85(modified_json)
        changes_log.append({
            "operation": "INSERT_NM1_82_FROM_85",
            "meta": meta,
            "timestamp": datetime.utcnow(),
            "fixId": request.fixId,
        })

        corrected_edi = edi_generator(modified_json)
        after_issues = validator_agent(modified_json, transaction_type="auto")
        diff = _diff_issues(before_issues, after_issues)

        fix_reports = session.get("fixReports") or []
        fix_reports.append({
            "timestamp": datetime.utcnow(),
            "type": "single",
            "applied": {
                "fixId": request.fixId,
                "operation": "INSERT_NM1_82_FROM_85",
                "meta": meta,
            },
            "fixMeta": {
                "id": fix_obj.get("id"),
                "errorId": fix_obj.get("errorId"),
                "description": fix_obj.get("description"),
                "reasoning": fix_obj.get("reasoning"),
                "fix_type": fix_obj.get("fix_type"),
                "confidence": fix_obj.get("confidence"),
                "auto_apply": fix_obj.get("auto_apply"),
            },
            "diff": diff,
        })

        status = "Clean" if len(after_issues or []) == 0 else "Requires Attention"

        # Mark accepted
        fixes = session.get("fixes") or []
        if request.fixId and isinstance(fixes, list):
            for f in fixes:
                if isinstance(f, dict) and f.get("id") == request.fixId:
                    f["status"] = "accepted"
                    break

        recomputed = pipeline_fix_agent({"errors": after_issues}, modified_json)
        remaining_error_ids = {str(e.get("id")) for e in (after_issues or []) if isinstance(e, dict) and e.get("id")}
        accepted = [
            f
            for f in (fixes or [])
            if isinstance(f, dict)
            and f.get("status") == "accepted"
            and str(f.get("errorId")) not in remaining_error_ids
        ]
        merged_fixes = accepted + (recomputed or [])

        sessions_collection.update_one(
            {"_id": obj_id},
            {"$set": {
                "modifiedJson": modified_json,
                "changesLog": changes_log,
                "correctedEdi": corrected_edi,
                "validationErrors": after_issues,
                "fixReports": fix_reports,
                "status": status,
                "fixes": merged_fixes,
                "updatedAt": datetime.utcnow(),
            }},
        )

        return {"message": "Fix applied", "sessionId": request.sessionId}

    # 3. Resolve target (explicit payload or session-stored fixId)
    segment_id, element_id, new_value, fix_obj_from_resolve = _resolve_fix_target(
        session,
        request.segmentId,
        request.elementId,
        request.newValue,
        request.fixId,
    )
    if fix_obj is None:
        fix_obj = fix_obj_from_resolve

    # 4. Modify "modifiedJson" assuming structured array configuration
    segments = modified_json.get("segments", [])
    old_value = None
    segment_found = False
    element_found = False
    
    # Safe array operation; when there are multiple segments with the same id,
    # prefer the one whose current value matches the fix's original value.
    original_hint = None
    if isinstance(fix_obj, dict) and fix_obj.get("original") not in (None, ""):
        original_hint = str(fix_obj.get("original"))

    for seg in segments:
        if str(seg.get("segmentId") or "").upper() != str(segment_id).upper():
            continue
        segment_found = True
        el = _find_element_in_segment(seg, element_id)
        if el is None:
            continue
        old_value = el.get("value")
        if original_hint is not None and str(old_value) != original_hint:
            # Not the intended occurrence; keep searching.
            continue
        el["value"] = new_value
        element_found = True
        break

    if not segment_found or not element_found:
        raise HTTPException(status_code=400, detail="Segment or element not found in session")

    # 5. Capture current issues (for report diff)
    before_issues = session.get("validationErrors") or []

    # 6. Append entry to "changesLog"
    changes_log = session.get("changesLog") or []
    changes_log.append({
        "segmentId": segment_id,
        "elementId": element_id,
        "old": old_value,
        "new": new_value,
        "timestamp": datetime.utcnow()
    })

    # 7. Regenerate corrected EDI
    corrected_edi = edi_generator(modified_json)

    # 6.5 Re-run validation logic to catch outstanding or cleared errors
    after_issues = validator_agent(modified_json, transaction_type="auto")
    diff = _diff_issues(before_issues, after_issues)

    # Try to attach the original fix suggestion description for auditability
    fix_meta = None
    if request.fixId and isinstance(fix_obj, dict):
        fix_meta = {
            "id": fix_obj.get("id"),
            "errorId": fix_obj.get("errorId"),
            "description": fix_obj.get("description"),
            "original": fix_obj.get("original"),
            "suggested": fix_obj.get("suggested"),
        }

    fix_reports = session.get("fixReports") or []
    fix_reports.append({
        "timestamp": datetime.utcnow(),
        "type": "single",
        "applied": {
            "fixId": request.fixId,
            "segmentId": segment_id,
            "elementId": element_id,
            "oldValue": old_value,
            "newValue": new_value,
        },
        "fixMeta": fix_meta,
        "diff": diff,
    })

    status = "Clean" if len(after_issues or []) == 0 else "Requires Attention"

    # Mark accepted on the stored fix list (if present)
    fixes = session.get("fixes") or []
    if request.fixId and isinstance(fixes, list):
        for fix in fixes:
            if isinstance(fix, dict) and fix.get("id") == request.fixId:
                fix["status"] = "accepted"
                break

    # Recompute fix suggestions from latest validation issues so UI stays in sync
    recomputed = pipeline_fix_agent({"errors": after_issues}, modified_json)
    remaining_error_ids = {str(e.get("id")) for e in (after_issues or []) if isinstance(e, dict) and e.get("id")}
    accepted = [
        f
        for f in (fixes or [])
        if isinstance(f, dict)
        and f.get("status") == "accepted"
        and str(f.get("errorId")) not in remaining_error_ids
    ]
    merged_fixes = accepted + (recomputed or [])

    # 6. Update Mongo
    update_fields = {
        "modifiedJson": modified_json,
        "changesLog": changes_log,
        "correctedEdi": corrected_edi,
        # Current issues update; originalValidationErrors remains unchanged.
        "validationErrors": after_issues,
        "fixReports": fix_reports,
        "status": status,
        "fixes": merged_fixes,
        "updatedAt": datetime.utcnow()
    }

    sessions_collection.update_one(
        {"_id": obj_id},
        {"$set": update_fields}
    )

    # 7. Return mapping
    return {
        "message": "Fix applied",
        "sessionId": request.sessionId
    }


@router.post("/apply-batch")
async def apply_fix_batch(request: ApplyFixBatchRequest, current_user: dict = Depends(get_current_user)):
    """Apply multiple element changes in a single transaction and produce a single report entry."""
    try:
        obj_id = ObjectId(request.sessionId)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    if sessions_collection is None:
        raise HTTPException(status_code=503, detail="Database connection not configured")

    session = sessions_collection.find_one({"_id": obj_id, "userId": current_user["userId"]})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Backfill originalValidationErrors for legacy sessions
    if session.get("originalValidationErrors") is None:
        try:
            sessions_collection.update_one(
                {"_id": obj_id},
                {"$set": {"originalValidationErrors": session.get("validationErrors") or [], "updatedAt": datetime.utcnow()}},
            )
        except Exception:
            pass

    modified_json = session.get("modifiedJson") or {}
    segments = modified_json.get("segments", [])
    before_issues = session.get("validationErrors") or []
    changes_log = session.get("changesLog") or []

    fixes_by_id = {f.get("id"): f for f in (session.get("fixes") or []) if isinstance(f, dict) and f.get("id")}
    applied_items = []
    for item in request.fixes or []:
        # Resolve any missing targeting from fixId
        try:
            segment_id, element_id, new_value, fix_obj = _resolve_fix_target(
                session,
                item.segmentId,
                item.elementId,
                item.newValue,
                item.fixId,
            )
        except HTTPException as ex:
            applied_items.append({
                "fixId": item.fixId,
                "segmentId": item.segmentId,
                "elementId": item.elementId,
                "status": "skipped",
                "reason": ex.detail,
            })
            continue

        old_value = None
        segment_found = False
        element_found = False
        fix_meta_obj = fixes_by_id.get(item.fixId) if item.fixId else None
        original_hint = None
        if isinstance(fix_meta_obj, dict) and fix_meta_obj.get("original") not in (None, ""):
            original_hint = str(fix_meta_obj.get("original"))

        for seg in segments:
            if str(seg.get("segmentId") or "").upper() != str(segment_id).upper():
                continue
            segment_found = True
            el = _find_element_in_segment(seg, element_id)
            if el is None:
                continue
            old_value = el.get("value")
            if original_hint is not None and str(old_value) != original_hint:
                continue
            el["value"] = new_value
            element_found = True
            break

        if not segment_found or not element_found:
            # Skip invalid fix items; keep batch resilient.
            applied_items.append({
                "fixId": item.fixId,
                "segmentId": segment_id,
                "elementId": element_id,
                "status": "skipped",
                "reason": "Segment or element not found",
            })
            continue

        changes_log.append({
            "segmentId": segment_id,
            "elementId": element_id,
            "old": old_value,
            "new": new_value,
            "timestamp": datetime.utcnow(),
            "fixId": item.fixId,
        })

        meta = fix_meta_obj
        applied_items.append({
            "fixId": item.fixId,
            "segmentId": segment_id,
            "elementId": element_id,
            "oldValue": old_value,
            "newValue": new_value,
            "status": "applied",
            "fixMeta": {
                "id": meta.get("id"),
                "errorId": meta.get("errorId"),
                "description": meta.get("description"),
                "original": meta.get("original"),
                "suggested": meta.get("suggested"),
            } if isinstance(meta, dict) else None,
        })

    corrected_edi = edi_generator(modified_json)
    after_issues = validator_agent(modified_json, transaction_type="auto")
    diff = _diff_issues(before_issues, after_issues)

    fix_reports = session.get("fixReports") or []
    fix_reports.append({
        "timestamp": datetime.utcnow(),
        "type": "batch",
        "applied": applied_items,
        "diff": diff,
    })

    status = "Clean" if len(after_issues or []) == 0 else "Requires Attention"

    update_fields = {
        "modifiedJson": modified_json,
        "changesLog": changes_log,
        "correctedEdi": corrected_edi,
        "validationErrors": after_issues,
        "fixReports": fix_reports,
        "status": status,
        "updatedAt": datetime.utcnow(),
    }

    # Mark provided fixIds as accepted
    fix_ids = {f.fixId for f in (request.fixes or []) if f.fixId}
    fixes = session.get("fixes") or []
    if fix_ids and isinstance(fixes, list):
        for f in fixes:
            if isinstance(f, dict) and f.get("id") in fix_ids:
                f["status"] = "accepted"

    # Recompute fix suggestions from latest validation issues so UI stays in sync
    recomputed = pipeline_fix_agent({"errors": after_issues}, modified_json)
    remaining_error_ids = {str(e.get("id")) for e in (after_issues or []) if isinstance(e, dict) and e.get("id")}
    accepted = [
        f
        for f in (fixes or [])
        if isinstance(f, dict)
        and f.get("status") == "accepted"
        and str(f.get("errorId")) not in remaining_error_ids
    ]
    update_fields["fixes"] = accepted + (recomputed or [])

    sessions_collection.update_one({"_id": obj_id}, {"$set": update_fields})

    return {
        "message": "Batch fixes applied",
        "sessionId": request.sessionId,
        "appliedCount": sum(1 for a in applied_items if a.get("status") == "applied"),
        "skippedCount": sum(1 for a in applied_items if a.get("status") == "skipped"),
        "status": status,
    }
