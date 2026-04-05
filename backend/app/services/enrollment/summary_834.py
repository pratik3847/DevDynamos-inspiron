"""834 enrollment summary helpers for dashboard consumption."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def _get_element_value(segment: Dict[str, Any], position: int) -> str:
    elements = segment.get("elements") or []
    pos = str(position).zfill(2)

    for el in elements:
        if str(el.get("position")) == pos:
            return str(el.get("value") or "").strip()

    idx = position - 1
    if 0 <= idx < len(elements):
        return str(elements[idx].get("value") or "").strip()

    return ""


def _member_name_and_id(block: List[Dict[str, Any]]) -> Dict[str, str]:
    nm1 = next((seg for seg in block if seg.get("segmentId") == "NM1"), {})

    last_or_org = _get_element_value(nm1, 3)
    first = _get_element_value(nm1, 4)
    member_id_nm1 = _get_element_value(nm1, 9)

    name = ", ".join([v for v in [last_or_org, first] if v]).strip() or last_or_org or "Unknown Member"

    member_ref = next(
        (
            seg
            for seg in block
            if seg.get("segmentId") == "REF" and _get_element_value(seg, 1) == "0F"
        ),
        {},
    )
    member_id_ref = _get_element_value(member_ref, 2)

    return {
        "name": name,
        "memberId": member_id_ref or member_id_nm1 or "-",
    }


def _extract_member_blocks(segments: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    blocks: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []

    for seg in segments:
        if seg.get("segmentId") == "INS":
            if current:
                blocks.append(current)
            current = [seg]
        elif current:
            current.append(seg)

    if current:
        blocks.append(current)

    return blocks


def _has_cob(block: List[Dict[str, Any]]) -> bool:
    # Flat parser does not preserve loop nesting. Use pragmatic segment-level hints.
    for seg in block:
        seg_id = str(seg.get("segmentId") or "").upper()
        if seg_id in {"COB", "OI", "SBR"}:
            return True
        raw = str(seg.get("raw") or "")
        if "2320" in raw:
            return True
    return False


def _maintenance_label(code: str) -> str:
    mapping = {
        "021": "Addition",
        "024": "Cancellation",
        "001": "Change",
        "030": "Audit",
    }
    if code in mapping:
        return f"{code} {mapping[code]}"
    if code:
        return f"{code} Unknown"
    return "Unknown"


def build_834_member_enrollment_summary(parsed_json: Dict[str, Any]) -> Dict[str, Any]:
    """Build a family/subscriber/dependent summary from flat parsed segments.

    Designed for 834 Loop 2000 style data used by Dashboard 835 page.
    """
    segments = parsed_json.get("segments") if isinstance(parsed_json, dict) else []
    if not isinstance(segments, list):
        segments = []

    blocks = _extract_member_blocks(segments)

    parsed_members: List[Dict[str, Any]] = []
    for idx, block in enumerate(blocks):
        ins = block[0] if block else {}
        ins01 = _get_element_value(ins, 1)  # Subscriber indicator
        ins02 = _get_element_value(ins, 2)  # Relationship
        ins03 = _get_element_value(ins, 3)  # Maintenance type
        ident = _member_name_and_id(block)

        parsed_members.append(
            {
                "key": f"m_{idx}_{ident['memberId']}",
                "name": ident["name"],
                "memberId": ident["memberId"],
                "maintenanceCode": ins03,
                "maintenanceLabel": _maintenance_label(ins03),
                "relationshipCode": ins02 or ins01,
                "hasCob": _has_cob(block),
                "dependents": [],
                "familyGroup": "-",
            }
        )

    families: List[Dict[str, Any]] = []
    current_subscriber: Dict[str, Any] | None = None
    family_counter = 0

    for member in parsed_members:
        rel = str(member.get("relationshipCode") or "").upper()
        # INS01=Y means subscriber. INS02 commonly 18(self), 01(spouse in some feeds but seen as lead in practice).
        is_subscriber = rel in {"Y", "18", "01"}

        if is_subscriber or current_subscriber is None:
            family_counter += 1
            member["familyGroup"] = f"Family {family_counter}"
            families.append(member)
            current_subscriber = member
        else:
            member["familyGroup"] = current_subscriber["familyGroup"]
            current_subscriber["dependents"].append(member)

    total_dependents = sum(len(f.get("dependents") or []) for f in families)
    total_subscribers = len(families)
    total_members = total_subscribers + total_dependents
    total_cob = sum(
        (1 if f.get("hasCob") else 0)
        + sum(1 for d in (f.get("dependents") or []) if d.get("hasCob"))
        for f in families
    )

    return {
        "type": "834-member-enrollment-summary",
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "families": families,
        "stats": {
            "totalMembers": total_members,
            "totalSubscribers": total_subscribers,
            "totalDependents": total_dependents,
            "totalCob": total_cob,
            "familyCount": total_subscribers,
        },
    }
