from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (  # type: ignore
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


def _escape_pre(text: str) -> str:
    # reportlab Paragraph uses a small HTML subset; escape minimal characters.
    return (
        _safe_str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _escape_html(text: str) -> str:
    return (
        _safe_str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _safe_str(v: Any) -> str:
    if v is None:
        return ""
    try:
        return str(v)
    except Exception:
        return ""


def _compact_text(s: Any, max_len: int = 240) -> str:
    text = _safe_str(s).replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _cell(text: Any, style: ParagraphStyle, max_len: int = 240) -> Paragraph:
    compact = _compact_text(text, max_len)
    return Paragraph(_escape_html(compact), style)


def _first_non_empty(*values: Any) -> str:
    for v in values:
        s = _safe_str(v).strip()
        if s:
            return s
    return ""


def _normalize_issue(err: Dict[str, Any]) -> Dict[str, str]:
    issue_id = _first_non_empty(err.get("id"), err.get("rule_id"), err.get("code"), "-")
    severity = _first_non_empty(err.get("severity"), "-").upper()
    layer = _first_non_empty(err.get("layer"), "-").upper()
    segment = _first_non_empty(err.get("segment"), "-").upper()
    element = _first_non_empty(err.get("field"), err.get("element"), "-").upper()
    desc = _first_non_empty(err.get("message"), err.get("error"), err.get("description"), "-")
    value = _first_non_empty(err.get("value"), "")
    return {
        "id": issue_id,
        "severity": severity,
        "layer": layer,
        "segment": segment,
        "element": element,
        "description": desc,
        "value": value,
    }


def _group_issues_by_layer(issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
    out: Dict[str, List[Dict[str, str]]] = {
        "STRUCTURAL": [],
        "BUSINESS": [],
        "EXTERNAL": [],
        "OTHER": [],
    }
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


def _classify_fix(f: Dict[str, Any]) -> str:
    fix_type = _safe_str(f.get("fix_type") or f.get("type") or "").upper()
    auto_apply = f.get("auto_apply")
    confidence = f.get("confidence")

    if auto_apply is True or "DETERMIN" in fix_type:
        return "auto"
    if "MANUAL" in fix_type:
        return "manual"
    try:
        if confidence is not None and float(confidence) <= 0:
            return "manual"
    except Exception:
        pass
    return "ai"


def _transaction_type_from_session(session: Dict[str, Any]) -> str:
    tx = _first_non_empty(
        session.get("transactionType"),
        session.get("transaction_type"),
        session.get("transaction"),
        (session.get("parsedJson") or {}).get("transactionType") if isinstance(session.get("parsedJson"), dict) else "",
    )
    txu = tx.upper().strip()
    if txu.startswith("837"):
        return "837"
    if txu.startswith("835"):
        return "835"
    if txu.startswith("834"):
        return "834"
    return txu or "-"


def _derive_overall_status(session: Dict[str, Any]) -> str:
    current_issues = session.get("validationErrors") or []
    corrected = _safe_str(session.get("correctedEdi") or "").strip()
    if not current_issues and corrected:
        return "Corrected"
    if not current_issues:
        return "Valid"
    return "Requires Attention"


def _count_errors_warnings(issues: List[Dict[str, str]]) -> Tuple[int, int]:
    errors = 0
    warnings = 0
    for e in issues:
        sev = (e.get("severity") or "").upper()
        if sev in {"WARNING", "INFO"}:
            warnings += 1
        else:
            errors += 1
    return errors, warnings


def _edi_segments(edi_text: str) -> List[str]:
    body = _safe_str(edi_text).replace("\r\n", "\n").replace("\r", "\n").strip()
    if not body:
        return []
    parts = [p.strip() for p in body.split("~")]
    return [p for p in parts if p]


def _edi_diff_lines(raw_edi: str, corrected_edi: str, *, max_lines: int = 260) -> List[str]:
    raw = _edi_segments(raw_edi)
    cor = _edi_segments(corrected_edi)
    if not cor and not raw:
        return ["(No EDI content available)"]
    if not cor:
        lines = [s + "~" for s in raw]
        if len(lines) > max_lines:
            lines = lines[:max_lines] + ["… (truncated)"]
        return lines

    out: List[str] = []
    n = min(len(raw), len(cor))
    for i in range(n):
        if raw[i] == cor[i]:
            out.append("  " + cor[i] + "~")
        else:
            out.append("+ " + cor[i] + "~")
            out.append("- " + raw[i] + "~")
    for i in range(n, len(cor)):
        out.append("+ " + cor[i] + "~")
    for i in range(n, len(raw)):
        out.append("- " + raw[i] + "~")
    if len(out) > max_lines:
        out = out[:max_lines] + ["… (truncated)"]
    return out


def build_fix_report_pdf(*, session: Dict[str, Any]) -> bytes:
    """Render a professional PDF report for a session.

    Includes:
    - Summary
    - Current validation issues
    - Auto-fix suggestions
    - Applied changes log
    """

    filename = _safe_str(session.get("fileName") or session.get("filename") or "file.edi")
    session_id = _safe_str(session.get("_id") or session.get("id") or "")
    tx_type = _transaction_type_from_session(session)
    overall_status = _derive_overall_status(session)

    validation_issues: List[Dict[str, Any]] = session.get("validationErrors") or []
    original_issues: List[Dict[str, Any]] = session.get("originalValidationErrors") or validation_issues
    fix_suggestions: List[Dict[str, Any]] = session.get("fixes") or []
    changes_log: List[Dict[str, Any]] = session.get("changesLog") or []
    corrected_edi = _safe_str(session.get("correctedEdi") or "")
    raw_edi = _safe_str(session.get("rawEdi") or "")

    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="EDI Validation & Auto-Fix Report",
        author="EDI Assistant",
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    h_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        spaceBefore=12,
        spaceAfter=6,
    )
    h3_style = ParagraphStyle(
        "SectionSubHeader",
        parent=styles["Heading3"],
        spaceBefore=8,
        spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        textColor=colors.HexColor("#4B5563"),
        fontSize=9,
        leading=12,
    )
    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        wordWrap="CJK",
    )
    cell_small_style = ParagraphStyle(
        "CellSmall",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=9,
        wordWrap="CJK",
    )
    header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontSize=9,
        leading=10,
        textColor=colors.white,
        alignment=1,
        fontName="Helvetica-Bold",
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
    )
    pre_style = ParagraphStyle(
        "Pre",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=9,
        wordWrap="CJK",
    )

    def _bullet_block(items: List[str]) -> Paragraph:
        text = "<br/>".join(f"- {_escape_html(item)}" for item in items)
        return Paragraph(text, small_style)

    story = []
    story.append(Paragraph("EDI Validation & Auto-Fix Report", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Timestamp (UTC): {_safe_str(datetime.utcnow().isoformat())}", meta_style))
    story.append(Paragraph(f"Session ID: {session_id}", meta_style))
    story.append(Paragraph(f"File Name: {filename}", meta_style))
    story.append(Paragraph(f"Transaction Type: {tx_type}", meta_style))
    story.append(Paragraph(f"Overall Status: {overall_status}", meta_style))
    story.append(Spacer(1, 14))

    # 2. Executive Summary
    story.append(Paragraph("Executive Summary", h_style))
    orig_norm = [_normalize_issue(e) for e in original_issues if isinstance(e, dict)]
    err_count, warn_count = _count_errors_warnings(orig_norm)

    classified = {"auto": [], "ai": [], "manual": []}
    for f in fix_suggestions or []:
        if not isinstance(f, dict):
            continue
        classified[_classify_fix(f)].append(f)

    auto_applied = [
        f for f in classified["auto"]
        if isinstance(f, dict) and _safe_str(f.get("status")).lower() == "accepted"
    ]

    summary_data = [
        ["Total issues detected (uploaded file)", str(len(orig_norm))],
        ["Errors", str(err_count)],
        ["Warnings", str(warn_count)],
        ["Auto-fixed issues (applied)", str(len(auto_applied))],
        ["AI-suggested fixes (approval required)", str(len(classified["ai"]))],
        ["Manual review required", str(len(classified["manual"]))],
        ["Final status", overall_status],
    ]
    summary_table = Table(summary_data, colWidths=[3.7 * inch, 1.9 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)

    story.append(Spacer(1, 10))
    if overall_status == "Corrected":
        story.append(Paragraph("Final status: Corrected output produced and no remaining validation issues.", small_style))
    elif overall_status == "Valid":
        story.append(Paragraph("Final status: No validation issues were detected.", small_style))
    else:
        story.append(Paragraph("Final status: Remaining issues require attention before the EDI can be considered compliant.", small_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("How to Use This Report", h3_style))
    story.append(
        _bullet_block(
            [
                "Start with Structural issues first; they can invalidate the entire file.",
                "Review Business and External issues next, prioritizing Critical and Error severity.",
                "Apply deterministic fixes first, then review AI suggestions, and flag manual items for payer review.",
            ]
        )
    )

    # 3. Validation Results (grouped)
    story.append(Spacer(1, 14))
    story.append(Paragraph("Validation Results", h_style))
    story.append(Paragraph("Issues are grouped by layer to speed up triage.", small_style))

    grouped = _group_issues_by_layer(original_issues)

    def _issues_table(title: str, items: List[Dict[str, str]]):
        story.append(Spacer(1, 10))
        story.append(Paragraph(title, h_style))
        if not items:
            story.append(Paragraph("No issues found.", small_style))
            return
        rows = [[
            Paragraph("ID", header_style),
            Paragraph("Severity", header_style),
            Paragraph("Layer", header_style),
            Paragraph("Segment", header_style),
            Paragraph("Element", header_style),
            Paragraph("Description", header_style),
        ]]
        for it in items[:250]:
            rows.append(
                [
                    _cell(it.get("id"), cell_style, 30),
                    _cell(it.get("severity"), cell_style, 12),
                    _cell(it.get("layer"), cell_style, 12),
                    _cell(it.get("segment"), cell_style, 12),
                    _cell(it.get("element"), cell_style, 12),
                    _cell(it.get("description"), cell_style, 240),
                ]
            )
        tbl = Table(
            rows,
            colWidths=[0.9 * inch, 0.7 * inch, 0.75 * inch, 0.6 * inch, 0.7 * inch, 2.85 * inch],
            repeatRows=1,
        )
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(tbl)
        if len(items) > 250:
            story.append(Spacer(1, 6))
            story.append(Paragraph("(Truncated to first 250 issues)", meta_style))

    _issues_table("Structural Issues", grouped.get("STRUCTURAL") or [])
    _issues_table("Business Rule Issues", grouped.get("BUSINESS") or [])
    _issues_table("External Validation Issues", grouped.get("EXTERNAL") or [])
    if grouped.get("OTHER"):
        _issues_table("Other Issues", grouped.get("OTHER") or [])

    story.append(PageBreak())

    # 4. Fix Classification Summary
    story.append(Paragraph("Fix Classification Summary", h_style))
    story.append(Paragraph("Use this section to prioritize fixes by automation level.", small_style))
    if not fix_suggestions:
        story.append(Paragraph("No fix suggestions available.", small_style))
    else:
        auto_fixes = [f for f in fix_suggestions if isinstance(f, dict) and _classify_fix(f) == "auto"]
        ai_fixes = [f for f in fix_suggestions if isinstance(f, dict) and _classify_fix(f) == "ai"]
        manual_fixes = [f for f in fix_suggestions if isinstance(f, dict) and _classify_fix(f) == "manual"]

        story.append(Spacer(1, 10))
        story.append(Paragraph("Automatically Applied Fixes", h_style))
        if not auto_fixes:
            story.append(Paragraph("No deterministic fixes available.", small_style))
        else:
            rows = [[
                Paragraph("Fix ID", header_style),
                Paragraph("Target", header_style),
                Paragraph("Before", header_style),
                Paragraph("After", header_style),
                Paragraph("Status", header_style),
            ]]
            for f in auto_fixes[:200]:
                target = f"{_safe_str(f.get('segmentId') or f.get('segment'))} · {_safe_str(f.get('elementId') or f.get('element') or f.get('field'))}"
                rows.append(
                    [
                        _cell(f.get("id"), cell_style, 30),
                        _cell(target, cell_style, 40),
                        _cell(f.get("original"), cell_style, 30),
                        _cell(f.get("suggested"), cell_style, 30),
                        _cell(f.get("status"), cell_style, 12),
                    ]
                )
            tbl = Table(rows, colWidths=[0.9 * inch, 1.5 * inch, 1.2 * inch, 1.2 * inch, 0.8 * inch], repeatRows=1)
            tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(tbl)

        story.append(Spacer(1, 10))
        story.append(Paragraph("AI-Suggested Fixes (Approval Required)", h_style))
        if not ai_fixes:
            story.append(Paragraph("No AI-suggested fixes pending approval.", small_style))
        else:
            rows = [[
                Paragraph("Fix ID", header_style),
                Paragraph("Confidence", header_style),
                Paragraph("Target", header_style),
                Paragraph("Suggested Action", header_style),
                Paragraph("Reasoning", header_style),
            ]]
            for f in ai_fixes[:200]:
                target = f"{_safe_str(f.get('segmentId') or f.get('segment'))} · {_safe_str(f.get('elementId') or f.get('element') or f.get('field'))}"
                action = _safe_str(f.get("operation") or "Update element")
                rows.append(
                    [
                        _cell(f.get("id"), cell_style, 30),
                        _cell(f.get("confidence"), cell_style, 12),
                        _cell(target, cell_style, 36),
                        _cell(action, cell_style, 36),
                        _cell(f.get("reasoning"), cell_style, 260),
                    ]
                )
            tbl = Table(rows, colWidths=[0.9 * inch, 0.8 * inch, 1.35 * inch, 1.25 * inch, 1.25 * inch], repeatRows=1)
            tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(tbl)

        story.append(Spacer(1, 10))
        story.append(Paragraph("Manual Review Required (Critical)", h_style))
        if not manual_fixes:
            story.append(Paragraph("No manual review items identified.", small_style))
        else:
            story.append(Paragraph("These items cannot be safely auto-fixed and require human validation.", small_style))
            rows = [[
                Paragraph("Issue ID", header_style),
                Paragraph("Target", header_style),
                Paragraph("Message", header_style),
                Paragraph("Current Value", header_style),
                Paragraph("Why not auto-fixed", header_style),
                Paragraph("Recommended Action", header_style),
            ]]
            issues_by_id = {str(i.get("id")): i for i in orig_norm if i.get("id")}
            for f in manual_fixes[:200]:
                err_id = _safe_str(f.get("errorId") or "")
                issue = issues_by_id.get(err_id, {})
                target = f"{_safe_str(issue.get('segment') or f.get('segmentId') or f.get('segment'))} · {_safe_str(issue.get('element') or issue.get('field') or f.get('elementId') or f.get('element') or f.get('field'))}"
                msg = _safe_str(issue.get("description") or issue.get("message") or issue.get("error") or f.get("description"))
                cur = _safe_str(issue.get("value") or f.get("original") or "")
                why = _safe_str(f.get("reasoning") or "Cannot derive a safe replacement value from EDI alone.")
                rec = "Verify using authoritative source (registry/payer rules) and update accordingly."
                rows.append(
                    [
                        _cell(err_id, cell_small_style, 30),
                        _cell(target, cell_small_style, 40),
                        _cell(msg, cell_small_style, 180),
                        _cell(cur, cell_small_style, 40),
                        _cell(why, cell_small_style, 180),
                        _cell(rec, cell_small_style, 120),
                    ]
                )
            tbl = Table(rows, colWidths=[0.8 * inch, 1.0 * inch, 1.45 * inch, 0.85 * inch, 1.35 * inch, 1.05 * inch], repeatRows=1)
            tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7F1D1D")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FEF2F2")),
                    ]
                )
            )
            story.append(tbl)

        # 5. Detailed Fix Cards (AI + Manual)
        story.append(PageBreak())
        story.append(Paragraph("Detailed Fix Cards", h_style))
        issues_by_id = {str(i.get("id")): i for i in orig_norm if i.get("id")}

        def _fix_card(f: Dict[str, Any]):
            err_id = _safe_str(f.get("errorId") or "")
            issue = issues_by_id.get(err_id, {})
            seg = _safe_str(issue.get("segment") or f.get("segmentId") or f.get("segment") or "-")
            el = _safe_str(issue.get("element") or issue.get("field") or f.get("elementId") or f.get("element") or f.get("field") or "-")
            conf = _safe_str(f.get("confidence") if f.get("confidence") is not None else "0")
            classification = _classify_fix(f)
            auto_fix_label = "Yes" if classification == "auto" else "No"
            if classification == "manual":
                auto_fix_label = "Not Possible"

            rows = [
                [Paragraph("Issue ID", label_style), _cell(err_id or "-", cell_style, 80)],
                [Paragraph("Segment · Element", label_style), _cell(f"{seg} · {el}", cell_style, 160)],
                [Paragraph("Confidence", label_style), _cell(conf + "%", cell_style, 40)],
                [Paragraph("Validation Issue", label_style), _cell(issue.get("description") or "-", cell_style, 320)],
                [Paragraph("Suggested Fix", label_style), _cell(_safe_str(f.get("operation") or "Update element value"), cell_style, 260)],
                [Paragraph("Reasoning", label_style), _cell(_safe_str(f.get("reasoning") or "-"), cell_style, 320)],
                [Paragraph("Current Value", label_style), _cell(_safe_str(issue.get("value") or f.get("original") or "-"), cell_style, 260)],
                [Paragraph("Replacement Value", label_style), _cell(_safe_str(f.get("suggested") or "-"), cell_style, 260)],
                [Paragraph("Auto Fix", label_style), _cell(auto_fix_label, cell_style, 60)],
            ]
            card = Table(rows, colWidths=[1.5 * inch, 4.1 * inch])
            bg = colors.HexColor("#FEF2F2") if classification == "manual" else colors.HexColor("#F9FAFB")
            card.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                        ("BACKGROUND", (0, 0), (-1, -1), bg),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(Spacer(1, 8))
            story.append(card)

        # Manual first, then AI
        for f in (manual_fixes[:20] + ai_fixes[:30]):
            if isinstance(f, dict):
                _fix_card(f)

    story.append(PageBreak())
    story.append(Paragraph("Changes Log", h_style))
    if not changes_log:
        story.append(Paragraph("No changes applied yet.", small_style))
    else:
        changes_rows = [[
            Paragraph("Timestamp", header_style),
            Paragraph("Target", header_style),
            Paragraph("Old", header_style),
            Paragraph("New", header_style),
        ]]
        for c in changes_log[:300]:
            if not isinstance(c, dict):
                continue
            ts = c.get("timestamp")
            if isinstance(ts, datetime):
                ts_str = ts.isoformat()
            else:
                ts_str = _safe_str(ts)
            target = f"{_safe_str(c.get('segmentId'))} · {_safe_str(c.get('elementId'))}"
            changes_rows.append(
                [
                    _cell(ts_str, cell_style, 40),
                    _cell(target, cell_style, 40),
                    _cell(c.get("old"), cell_style, 60),
                    _cell(c.get("new"), cell_style, 60),
                ]
            )

        changes_table = Table(
            changes_rows,
            colWidths=[1.5 * inch, 1.0 * inch, 1.75 * inch, 1.75 * inch],
            repeatRows=1,
        )
        changes_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(changes_table)
        if len(changes_log) > 300:
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"(Truncated to first 300 changes)", meta_style))

    # 7. Corrected EDI Output
    story.append(PageBreak())
    story.append(Paragraph("Corrected EDI Output", h_style))
    if not (corrected_edi.strip() or raw_edi.strip()):
        story.append(Paragraph("No EDI content available.", small_style))
    else:
        label = "Corrected vs Uploaded (diff-style, truncated)" if corrected_edi.strip() else "Uploaded Raw EDI (truncated)"
        story.append(Paragraph(label, meta_style))
        lines = _edi_diff_lines(raw_edi, corrected_edi)
        # Keep PDF size reasonable
        joined = "\n".join(lines)
        max_chars = 14000
        truncated = joined[:max_chars]
        if len(joined) > max_chars:
            truncated += "\n… (truncated)"
        pre = _escape_pre(truncated).replace("\n", "<br/>")
        story.append(Spacer(1, 8))
        story.append(Paragraph(pre, pre_style))

    # 8. Technical Insights
    story.append(Spacer(1, 14))
    story.append(Paragraph("Technical Insights", h_style))

    layer_counts = {
        "STRUCTURAL": len(grouped.get("STRUCTURAL") or []),
        "BUSINESS": len(grouped.get("BUSINESS") or []),
        "EXTERNAL": len(grouped.get("EXTERNAL") or []),
        "OTHER": len(grouped.get("OTHER") or []),
    }
    major_layer = max(layer_counts.items(), key=lambda kv: kv[1])[0] if orig_norm else "-"
    insights = []
    insights.append("Root-cause summary (best-effort):")
    if major_layer == "STRUCTURAL":
        insights.append("• Most issues are structural (envelope counts, required segments, control numbers, segment counts).")
    elif major_layer == "BUSINESS":
        insights.append("• Most issues are business-rule related (missing loops, qualifiers, required provider/patient fields).")
    elif major_layer == "EXTERNAL":
        insights.append("• Most issues are external-validation related (registry checks such as NPI and other identifiers).")
    else:
        insights.append("• Issues are mixed across validation layers.")
    if classified["manual"]:
        insights.append(f"• Human intervention required: {len(classified['manual'])} item(s) cannot be auto-fixed safely.")
    if classified["ai"]:
        insights.append(f"• AI review required: {len(classified['ai'])} suggested fix(es) require approval.")
    insights.append("Compliance notes (HIPAA/X12):")
    insights.append("• Validate ISA/IEA, GS/GE, ST/SE envelope integrity and transaction set counts.")
    insights.append("• Ensure provider identifiers (e.g., NPI) and payer-required values match authoritative sources.")
    insights.append("• External validation is advisory; final submission responsibility remains with the submitting entity.")

    story.append(Paragraph("<br/>".join(_escape_pre(x) for x in insights), small_style))

    doc.build(story)
    return buf.getvalue()
