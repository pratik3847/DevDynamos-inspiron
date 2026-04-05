from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import copy

from app.database import rules_collection


DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "id": "ISA13-IEA02",
        "name": "Interchange control numbers match",
        "category": "Structural",
        "severity": "Critical",
        "description": "ISA13 must match IEA02 to validate interchange boundaries.",
        "scope": ["837P", "835", "834"],
        "source": "HIPAA X12",
        "tags": ["Envelope", "Control"],
        "enabled": True,
        "defaultEnabled": True,
        "runtime": "Realtime",
        "lastUpdated": "2026-03-28",
        "matchCodes": ["ISA13_IEA02"],
    },
    {
        "id": "GS06-GE02",
        "name": "Functional group control alignment",
        "category": "Structural",
        "severity": "Error",
        "description": "GS06 must match GE02 to keep group counts aligned.",
        "scope": ["837P", "835", "834"],
        "source": "HIPAA X12",
        "tags": ["Group", "Control"],
        "enabled": True,
        "defaultEnabled": True,
        "runtime": "Realtime",
        "lastUpdated": "2026-03-29",
        "matchCodes": ["GS06_GE02"],
    },
    {
        "id": "SE01-SEGCOUNT",
        "name": "Segment count validation",
        "category": "Structural",
        "severity": "Error",
        "description": "SE01 must equal the number of segments from ST to SE.",
        "scope": ["837P", "835", "834"],
        "source": "HIPAA X12",
        "tags": ["Trailer", "Count"],
        "enabled": True,
        "defaultEnabled": True,
        "runtime": "Realtime",
        "lastUpdated": "2026-03-28",
        "matchCodes": ["SE01_SEGCOUNT"],
    },
    {
        "id": "NM1-85-REQUIRED",
        "name": "Billing provider required",
        "category": "Business",
        "severity": "Critical",
        "description": "NM1 segment with entity code 85 is required for all claims.",
        "scope": ["837P"],
        "source": "TR3 837P",
        "tags": ["Provider", "Required"],
        "enabled": True,
        "defaultEnabled": True,
        "runtime": "Realtime",
        "lastUpdated": "2026-03-27",
        "matchCodes": [],
    },
    {
        "id": "CLM-PRIORITY",
        "name": "Claim filing indicator check",
        "category": "Business",
        "severity": "Warning",
        "description": "CLM05-3 must be present when other payer info exists.",
        "scope": ["837P"],
        "source": "TR3 837P",
        "tags": ["Claim", "Coordination"],
        "enabled": True,
        "defaultEnabled": True,
        "runtime": "Realtime",
        "lastUpdated": "2026-03-24",
        "matchCodes": [],
    },
    {
        "id": "REF-EI-REQUIRED",
        "name": "Employer ID required for 834",
        "category": "Business",
        "severity": "Error",
        "description": "REF segment with qualifier EI must be present for sponsor.",
        "scope": ["834"],
        "source": "TR3 834",
        "tags": ["Sponsor", "Enrollment"],
        "enabled": True,
        "defaultEnabled": True,
        "runtime": "Realtime",
        "lastUpdated": "2026-03-18",
        "matchCodes": ["834_REQ_REF"],
    },
    {
        "id": "DTM-ESRD",
        "name": "ESRD date format enforcement",
        "category": "Business",
        "severity": "Warning",
        "description": "DTM segment must follow CCYYMMDD format for ESRD dates.",
        "scope": ["837P", "834"],
        "source": "Internal Policy",
        "tags": ["Dates", "Format"],
        "enabled": True,
        "defaultEnabled": True,
        "runtime": "Realtime",
        "lastUpdated": "2026-03-16",
        "matchCodes": ["DATE001", "DATE002"],
    },
    {
        "id": "NPI-ACTIVE",
        "name": "Provider NPI active in NPPES",
        "category": "External",
        "severity": "Error",
        "description": "NPI must resolve to an active provider record in NPPES.",
        "scope": ["837P", "835"],
        "source": "NPPES",
        "tags": ["Provider", "NPI"],
        "enabled": True,
        "defaultEnabled": True,
        "runtime": "External",
        "lastUpdated": "2026-03-22",
        "matchCodes": ["NPPES001", "NPPES002"],
    },
    {
        "id": "CODESET-ICD10",
        "name": "ICD-10 diagnosis code validation",
        "category": "External",
        "severity": "Error",
        "description": "Diagnosis codes must exist in the ICD-10 CM code set.",
        "scope": ["837P"],
        "source": "CMS Code Sets",
        "tags": ["Codes", "Clinical"],
        "enabled": True,
        "defaultEnabled": True,
        "runtime": "External",
        "lastUpdated": "2026-03-20",
        "matchCodes": ["ICD10_FMT001"],
    },
    {
        "id": "CODESET-HCPCS",
        "name": "HCPCS service code validation",
        "category": "External",
        "severity": "Warning",
        "description": "HCPCS service codes must be active for the service date.",
        "scope": ["837P"],
        "source": "CMS Code Sets",
        "tags": ["Codes", "Services"],
        "enabled": False,
        "defaultEnabled": False,
        "runtime": "External",
        "lastUpdated": "2026-03-15",
        "matchCodes": ["PROC_FMT001"],
    },
    {
        "id": "BPR02-AMOUNT",
        "name": "Payment amount precision check",
        "category": "Business",
        "severity": "Info",
        "description": "BPR02 must contain a valid monetary amount with 2 decimals.",
        "scope": ["835"],
        "source": "TR3 835",
        "tags": ["Payment", "Amount"],
        "enabled": True,
        "defaultEnabled": True,
        "runtime": "Realtime",
        "lastUpdated": "2026-03-10",
        "matchCodes": ["AMT001"],
    },
]


def _clone_rules() -> List[Dict[str, Any]]:
    return copy.deepcopy(DEFAULT_RULES)


def _serialize_timestamp(value: Optional[datetime]) -> Optional[str]:
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def get_or_create_user_rules(user_id: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    if rules_collection is None:
        return _clone_rules(), None

    doc = rules_collection.find_one({"userId": user_id})
    if not doc:
        now = datetime.utcnow()
        rules = _clone_rules()
        rules_collection.insert_one({
            "userId": user_id,
            "rules": rules,
            "createdAt": now,
            "updatedAt": now,
        })
        return rules, _serialize_timestamp(now)

    return doc.get("rules") or _clone_rules(), _serialize_timestamp(doc.get("updatedAt") or doc.get("createdAt"))


def save_user_rules(user_id: str, rules: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    if rules_collection is None:
        return rules, None

    now = datetime.utcnow()
    rules_collection.update_one(
        {"userId": user_id},
        {
            "$set": {
                "rules": rules,
                "updatedAt": now,
            },
            "$setOnInsert": {"createdAt": now},
        },
        upsert=True,
    )
    return rules, _serialize_timestamp(now)


def reset_user_rules(user_id: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    rules = _clone_rules()
    return save_user_rules(user_id, rules)


def build_disabled_rule_codes(rules: List[Dict[str, Any]]) -> List[str]:
    disabled_codes = set()
    for rule in rules or []:
        if rule.get("enabled") is True:
            continue
        match_codes = list(rule.get("matchCodes") or [])
        rule_id = rule.get("id")
        if rule_id:
            match_codes.append(rule_id)
        for code in match_codes:
            if code:
                disabled_codes.add(str(code))
    return sorted(disabled_codes)


def filter_issues_by_rules(issues: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    disabled_codes = set(build_disabled_rule_codes(rules))
    if not disabled_codes:
        return issues

    filtered: List[Dict[str, Any]] = []
    for issue in issues or []:
        if not isinstance(issue, dict):
            continue
        code = issue.get("rule_id") or issue.get("code") or issue.get("rule") or ""
        if code and str(code) in disabled_codes:
            continue
        filtered.append(issue)
    return filtered


def apply_rule_preferences(
    errors: List[Dict[str, Any]],
    warnings: List[Dict[str, Any]],
    user_id: Optional[str],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if not user_id:
        return errors, warnings

    rules, _ = get_or_create_user_rules(user_id)
    filtered_errors = filter_issues_by_rules(errors, rules)
    filtered_warnings = filter_issues_by_rules(warnings, rules)
    return filtered_errors, filtered_warnings
