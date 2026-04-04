from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _safe_str(v: Any) -> str:
    if v is None:
        return ""
    try:
        return str(v)
    except Exception:
        return ""


def _iso_now() -> str:
    return datetime.utcnow().isoformat()


def _first_non_empty(*values: Any) -> str:
    for v in values:
        s = _safe_str(v).strip()
        if s:
            return s
    return ""


def _compact(s: Any, max_len: int = 240) -> str:
    text = _safe_str(s).replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _md_escape(text: str) -> str:
    # Minimal escape for markdown tables.
    return _safe_str(text).replace("|", "\\|")


def _normalize_issue(err: Dict[str, Any]) -> Dict[str, str]:
    issue_id = _first_non_empty(err.get("id"), err.get("rule_id"), err.get("code"), "-")
    severity = _first_non_empty(err.get("severity"), "-").upper()
    layer = _first_non_empty(err.get("layer"), "-").upper()
    segment = _first_non_empty(err.get("segment"), "-").upper()
    element = _first_non_empty(err.get("field"), err.get("element"), "-").upper()
    desc = _first_non_empty(err.get("message"), err.get("error"), err.get("description"), "-")
    value = _first_non_empty(err.get("value"), err.get("currentValue"), "")
    return {
        "id": issue_id,
        "severity": severity,
        "layer": layer,
        "segment": segment,
        "element": element,
        "description": desc,
        "value": value,
    }


def _severity_bucket(sev: str) -> str:
    s = (sev or "").upper()
    if s in {"WARNING", "INFO"}:
        return "warning"
    return "error"


def _group_issues_by_layer(issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
    out = {"STRUCTURAL": [], "BUSINESS": [], "EXTERNAL": [], "OTHER": []}
    for e in issues or []:
        if not isinstance(e, dict):
            continue
        n = _normalize_issue(e)
        layer = (n.get("layer") or "").upper()
        if layer in out:
            out[layer].append(n)
        else:
            out["OTHER"].append(n)
    return out


def _normalize_fix(f: Dict[str, Any]) -> Dict[str, Any]:
    fix_id = _first_non_empty(f.get("id"), "-")
    fix_type = _first_non_empty(f.get("fix_type"), f.get("type"), "-")
    auto_apply = f.get("auto_apply")
    confidence = f.get("confidence")
    reasoning = _first_non_empty(f.get("reasoning"), "")
    status = _first_non_empty(f.get("status"), "")
    error_id = _first_non_empty(f.get("errorId"), f.get("error_id"), "")

    segment = _first_non_empty(f.get("segmentId"), f.get("segment"), "")
    element = _first_non_empty(f.get("elementId"), f.get("element"), f.get("field"), "")

    operation = _first_non_empty(f.get("operation"), "")

    original = f.get("original")
    suggested = f.get("suggested")

    return {
        "id": fix_id,
        "fix_type": str(fix_type),
        "auto_apply": auto_apply,
        "confidence": confidence,
        "reasoning": reasoning,
        "status": status,
        "errorId": str(error_id) if error_id else "",
        "segment": str(segment).upper() if segment else "",
        "element": str(element).upper() if element else "",
        "operation": str(operation).upper() if operation else "",
        "original": original,
        "suggested": suggested,
        "description": _first_non_empty(f.get("description"), ""),
    }


def _classify_fix(fix: Dict[str, Any]) -> str:
    fix_type = str(fix.get("fix_type") or "").upper()
    auto_apply = fix.get("auto_apply")
    confidence = fix.get("confidence")

    if auto_apply is True or "DETERMIN" in fix_type:
        return "auto"
    if "MANUAL" in fix_type:
        return "manual"
    try:
        if confidence is not None and float(confidence) <= 0:
            return "manual"
    except Exception:
        pass
    if "AI" in fix_type or "INFER" in fix_type:
        return "ai"
    # default: if it has reasoning/confidence, treat as AI-suggested
    if fix.get("reasoning"):
        return "ai"
    return "ai"


def _collect_applied_fix_ids(session: Dict[str, Any]) -> List[str]:
    applied: List[str] = []

    # Prefer fixReports because it stores fixId even when changesLog doesn't.
    for r in session.get("fixReports") or []:
        if not isinstance(r, dict):
            continue
        applied_obj = r.get("applied")
        if isinstance(applied_obj, dict):
            fid = applied_obj.get("fixId")
            if fid:
                applied.append(str(fid))
        elif isinstance(applied_obj, list):
            for item in applied_obj:
                if isinstance(item, dict) and item.get("fixId"):
                    applied.append(str(item.get("fixId")))

    # Fallback to changesLog fixId fields
    for c in session.get("changesLog") or []:
        if isinstance(c, dict) and c.get("fixId"):
            applied.append(str(c.get("fixId")))

    # Deduplicate in order
    seen = set()
    ordered = []
    for fid in applied:
        if fid in seen:
            continue
        seen.add(fid)
        ordered.append(fid)
    return ordered


def _derive_overall_status(session: Dict[str, Any]) -> str:
    current_issues = session.get("validationErrors") or []
    corrected = _safe_str(session.get("correctedEdi") or "").strip()
    if not current_issues and corrected:
        return "Corrected"
    if not current_issues:
        return "Valid"
    return "Requires Attention"


def _transaction_type_from_session(session: Dict[str, Any]) -> str:
    # Best-effort.
    tx = _first_non_empty(
        session.get("transactionType"),
        session.get("transaction_type"),
        session.get("transaction"),
        (session.get("parsedJson") or {}).get("transactionType") if isinstance(session.get("parsedJson"), dict) else "",
    )
    # Normalize common values
    txu = tx.upper().strip()
    if txu.startswith("837"):
        return "837"
    if txu.startswith("835"):
        return "835"
    if txu.startswith("834"):
        return "834"
    return txu or "-"


def _markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    header_line = "| " + " | ".join(_md_escape(h) for h in headers) + " |"
    sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = [
        "| " + " | ".join(_md_escape(c) for c in row) + " |" for row in rows
    ]
    return "\n".join([header_line, sep_line] + body_lines)


def _edi_segments(edi_text: str) -> List[str]:
    body = _safe_str(edi_text).replace("\r\n", "\n").replace("\r", "\n")
    body = body.strip()
    if not body:
        return []
    # Most X12 uses ~ segment terminator.
    parts = [p.strip() for p in body.split("~")]
    return [p for p in parts if p]


def _edi_diff_block(raw_edi: str, corrected_edi: str, *, max_lines: int = 220) -> str:
    raw = _edi_segments(raw_edi)
    cor = _edi_segments(corrected_edi)
    if not cor and not raw:
        return "````\n(No EDI content available)\n````"

    # If corrected missing, show raw.
    if not cor:
        lines = raw[:max_lines]
        return "```\n" + "\n".join(lines) + "\n```"

    # diff-like view: compare by index (best-effort highlight)
    out: List[str] = []
    n = min(len(raw), len(cor))
    for i in range(n):
        if raw[i] == cor[i]:
            out.append("  " + cor[i] + "~")
        else:
            out.append("+ " + cor[i] + "~")
            out.append("- " + raw[i] + "~")

    # Remaining
    for i in range(n, len(cor)):
        out.append("+ " + cor[i] + "~")
    for i in range(n, len(raw)):
        out.append("- " + raw[i] + "~")

    if len(out) > max_lines:
        out = out[:max_lines] + ["… (truncated)"]

    return "```diff\n" + "\n".join(out) + "\n```"


def build_fix_report_markdown(*, session: Dict[str, Any]) -> str:
    filename = _first_non_empty(session.get("fileName"), session.get("filename"), "file.edi")
    session_id = _first_non_empty(session.get("_id"), session.get("id"), "-")
    tx = _transaction_type_from_session(session)

    original_issues = session.get("originalValidationErrors") or session.get("validationErrors") or []
    current_issues = session.get("validationErrors") or []

    fixes_raw = [f for f in (session.get("fixes") or []) if isinstance(f, dict)]
    fixes = [_normalize_fix(f) for f in fixes_raw]

    applied_fix_ids = set(_collect_applied_fix_ids(session))

    # Counts
    orig_norm = [_normalize_issue(e) for e in original_issues if isinstance(e, dict)]
    current_norm = [_normalize_issue(e) for e in current_issues if isinstance(e, dict)]

    error_count = sum(1 for e in orig_norm if _severity_bucket(e.get("severity")) == "error")
    warn_count = sum(1 for e in orig_norm if _severity_bucket(e.get("severity")) == "warning")

    applied_fixes = [f for f in fixes if f.get("id") in applied_fix_ids]
    auto_applied = [f for f in applied_fixes if _classify_fix(f) == "auto"]
    ai_suggested = [f for f in fixes if _classify_fix(f) == "ai" and f.get("id") not in applied_fix_ids]
    manual_fixes = [f for f in fixes if _classify_fix(f) == "manual"]

    overall_status = _derive_overall_status(session)

    # Determine manual-review issues: any issue that has a manual fix, plus any issue with fixable==False and no auto fix
    manual_issue_ids = {str(f.get("errorId")) for f in manual_fixes if f.get("errorId")}
    manual_issue_ids = {i for i in manual_issue_ids if i and i != "-"}

    # Build report
    md: List[str] = []

    # 1. Header
    md.append("# EDI Validation & Auto-Fix Report")
    md.append("")
    md.append(_markdown_table(
        ["Field", "Value"],
        [
            ["Timestamp", _iso_now()],
            ["Session ID", _safe_str(session_id)],
            ["File Name", _safe_str(filename)],
            ["Transaction Type", _safe_str(tx)],
            ["Overall Status", _safe_str(overall_status)],
        ],
    ))

    # 2. Executive Summary
    md.append("")
    md.append("## Executive Summary")
    md.append("")
    md.append(_markdown_table(
        ["Metric", "Count"],
        [
            ["Total issues detected (uploaded file)", str(len(orig_norm))],
            ["Errors", str(error_count)],
            ["Warnings", str(warn_count)],
            ["✅ Auto-fixed issues (applied)", str(len(auto_applied))],
            ["💡 AI-suggested fixes (pending approval)", str(len(ai_suggested))],
            ["🔴 Manual review required", str(len(manual_fixes))],
        ],
    ))
    md.append("")
    if overall_status == "Corrected":
        md.append("Final status: The session has a corrected EDI output and no remaining validation issues.")
    elif overall_status == "Valid":
        md.append("Final status: No validation issues were detected.")
    else:
        md.append("Final status: Remaining issues require attention before the EDI can be considered compliant.")

    # 3. Validation Results
    md.append("")
    md.append("## Validation Results")
    md.append("")
    grouped = _group_issues_by_layer(original_issues)

    def issues_section(title: str, items: List[Dict[str, str]]) -> None:
        md.append(f"### {title}")
        md.append("")
        if not items:
            md.append("No issues found.")
            md.append("")
            return
        rows = []
        for it in items:
            rows.append([
                it.get("id", "-"),
                it.get("severity", "-"),
                it.get("layer", "-"),
                it.get("segment", "-"),
                it.get("element", "-"),
                _compact(it.get("description"), 160),
            ])
        md.append(_markdown_table(
            ["ID", "Severity", "Layer", "Segment", "Element", "Description"],
            rows,
        ))
        md.append("")

    issues_section("Structural Issues", grouped.get("STRUCTURAL", []))
    issues_section("Business Rule Issues", grouped.get("BUSINESS", []))
    issues_section("External Validation Issues", grouped.get("EXTERNAL", []))
    if grouped.get("OTHER"):
        issues_section("Other Issues", grouped.get("OTHER", []))

    # 4. Fix Classification Summary
    md.append("## Fix Classification Summary")
    md.append("")

    # A) Auto-applied fixes
    md.append("### ✅ Automatically Applied Fixes")
    md.append("")
    if not auto_applied:
        md.append("No deterministic fixes have been applied in this session.")
        md.append("")
    else:
        rows = []
        for f in auto_applied:
            target = " · ".join([p for p in [f.get("segment"), f.get("element")] if p]) or "-"
            before = _safe_str(f.get("original"))
            after = _safe_str(f.get("suggested"))
            rows.append([f.get("id", "-"), target, before, after])
        md.append(_markdown_table(["Fix ID", "Target", "Before", "After"], rows))
        md.append("")

    # B) AI suggested fixes
    md.append("### 💡 AI-Suggested Fixes (User Approval Required)")
    md.append("")
    if not ai_suggested:
        md.append("No AI-suggested fixes are pending approval.")
        md.append("")
    else:
        rows = []
        for f in ai_suggested[:200]:
            target = " · ".join([p for p in [f.get("segment"), f.get("element")] if p]) or "-"
            conf = _safe_str(f.get("confidence") or "")
            action = f.get("operation") or "Update element"
            reason = _compact(f.get("reasoning"), 120)
            rows.append([f.get("id", "-"), conf, target, action, reason])
        md.append(_markdown_table(["Fix ID", "Confidence %", "Target", "Suggested Action", "Reasoning"], rows))
        md.append("")

    # C) Manual review required
    md.append("### 🔴 Manual Review Required (Critical)")
    md.append("")
    if not manual_fixes:
        md.append("No manual-review items were identified by the fix engine.")
        md.append("")
    else:
        md.append("The following items cannot be safely auto-fixed and require human confirmation or external source data.")
        md.append("")
        rows = []
        # Link manual fixes back to issues when possible
        issues_by_id = {str(i.get("id")): i for i in orig_norm if i.get("id")}
        for f in manual_fixes[:200]:
            err_id = str(f.get("errorId") or "").strip()
            issue = issues_by_id.get(err_id, {})
            target = " · ".join([p for p in [issue.get("segment"), issue.get("element")] if p]) or "-"
            msg = _compact(issue.get("description") or f.get("description"), 140)
            current_val = _compact(issue.get("value") or f.get("original"), 40)
            why = _compact(f.get("reasoning") or "Cannot derive a safe replacement value from EDI alone.", 120)
            rec = "Verify against authoritative source (e.g., provider registry / payer requirements) and update accordingly."
            rows.append([err_id or "-", target, msg, current_val, why, rec])
        md.append(_markdown_table(
            ["Issue ID", "Segment · Element", "Validation Message", "Current Value", "Why not auto-fixed", "Recommended Action"],
            rows,
        ))
        md.append("")

    # 5. Detailed Fix Cards
    md.append("## Detailed Fix Cards")
    md.append("")
    issues_map = {str(i.get("id")): i for i in orig_norm if i.get("id")}

    def fix_card(icon: str, f: Dict[str, Any]) -> None:
        fid = _safe_str(f.get("id"))
        err_id = _safe_str(f.get("errorId"))
        issue = issues_map.get(err_id, {})
        seg = _first_non_empty(issue.get("segment"), f.get("segment"), "-")
        el = _first_non_empty(issue.get("element"), f.get("element"), "-")
        conf = _safe_str(f.get("confidence") if f.get("confidence") is not None else "0")
        auto_fix = "Yes" if _classify_fix(f) == "auto" else "No"
        if _classify_fix(f) == "manual":
            auto_fix = "❌ Not Possible"

        md.append(f"### {icon} Issue {err_id or '-'} — Fix {fid}")
        md.append("")
        md.append(_markdown_table(
            ["Field", "Value"],
            [
                ["Segment", f"{seg}"],
                ["Element", f"{el}"],
                ["Confidence", f"{conf}%"],
                ["Validation Issue", _compact(issue.get("description") or "-", 220)],
                ["Suggested Fix", _compact(f.get("operation") or "Update element value", 220)],
                ["Reasoning", _compact(f.get("reasoning") or "-", 320)],
                ["Current Value", _compact(issue.get("value") or f.get("original") or "-", 220)],
                ["Replacement Value", _compact(f.get("suggested") or "-", 220)],
                ["Auto Fix", auto_fix],
            ],
        ))
        md.append("")

    # Cards for AI + Manual first
    for f in (manual_fixes[:40] + ai_suggested[:60]):
        icon = "🔴" if _classify_fix(f) == "manual" else "💡"
        fix_card(icon, f)

    # 6. Change Log
    md.append("## Change Log")
    md.append("")
    changes = [c for c in (session.get("changesLog") or []) if isinstance(c, dict)]
    if not changes:
        md.append("No changes have been applied yet.")
        md.append("")
    else:
        rows = []
        for c in changes[:400]:
            ts = c.get("timestamp")
            ts_str = ts.isoformat() if isinstance(ts, datetime) else _safe_str(ts)
            if c.get("operation"):
                target = _safe_str(c.get("operation"))
                old = _compact(c.get("meta") or "", 60)
                new = "(operation applied)"
            else:
                target = f"{_safe_str(c.get('segmentId'))} · {_safe_str(c.get('elementId'))}"
                old = _compact(c.get("old"), 60)
                new = _compact(c.get("new"), 60)
            rows.append([ts_str, target, old, new])
        md.append(_markdown_table(["Timestamp", "Segment · Element", "Old Value", "New Value"], rows))
        md.append("")

    # 7. Corrected EDI Output
    md.append("## Corrected EDI Output")
    md.append("")
    raw_edi = _safe_str(session.get("rawEdi") or "")
    corrected_edi = _safe_str(session.get("correctedEdi") or "")
    if not corrected_edi.strip():
        md.append("No corrected EDI is available yet; showing uploaded EDI.")
        md.append("")
    md.append(_edi_diff_block(raw_edi, corrected_edi, max_lines=260))

    # 8. Technical Insights
    md.append("")
    md.append("## Technical Insights")
    md.append("")

    # Root-cause hints based on layer counts
    layer_counts = {"STRUCTURAL": 0, "BUSINESS": 0, "EXTERNAL": 0, "OTHER": 0}
    for it in orig_norm:
        layer = (it.get("layer") or "OTHER").upper()
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    major_layer = max(layer_counts.items(), key=lambda kv: kv[1])[0] if orig_norm else "-"

    md.append("- Root-cause summary (best-effort):")
    if major_layer == "STRUCTURAL":
        md.append("  - Most issues are structural (envelope counts, required segments, control numbers, or segment counts).")
    elif major_layer == "BUSINESS":
        md.append("  - Most issues are business-rule related (missing loops, qualifiers, or required provider/patient fields).")
    elif major_layer == "EXTERNAL":
        md.append("  - Most issues are external-validation related (registry lookups such as NPI and other identifiers).")
    else:
        md.append("  - Issues are mixed across layers.")

    if manual_fixes:
        md.append(f"- Human intervention required: {len(manual_fixes)} item(s) cannot be auto-fixed safely.")
    if ai_suggested:
        md.append(f"- AI review required: {len(ai_suggested)} suggested fix(es) pending approval.")

    md.append("- Compliance notes (HIPAA/X12):")
    md.append("  - Validate X12 envelope integrity (ISA/IEA, GS/GE, ST/SE) and transaction set counts.")
    md.append("  - Ensure provider identifiers (e.g., NPI) and payer-required fields match authoritative sources.")
    md.append("  - Use external validation results as advisory; final responsibility remains with submitting entity.")

    md.append("")
    md.append("---")
    md.append("Generated by EDI validation & auto-fix engine.")

    return "\n".join(md)


def build_fix_report_html(*, session: Dict[str, Any]) -> str:
    # Simple HTML wrapper around the Markdown for easy PDF conversion by external tools.
    md = build_fix_report_markdown(session=session)
    escaped = (
        md.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        "<!doctype html>\n"
        "<html><head><meta charset='utf-8'/>"
        "<title>EDI Validation & Auto-Fix Report</title>"
        "<style>body{font-family:Arial,Helvetica,sans-serif;line-height:1.4;max-width:960px;margin:24px auto;padding:0 16px;}"
        "pre{white-space:pre-wrap;word-break:break-word;background:#f6f8fa;padding:12px;border-radius:6px;}"
        "</style></head><body>"
        "<pre>" + escaped + "</pre>"
        "</body></html>"
    )
