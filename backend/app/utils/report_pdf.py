from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List

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


def build_fix_report_pdf(*, session: Dict[str, Any]) -> bytes:
    """Render a professional PDF report for a session.

    Includes:
    - Summary
    - Current validation issues
    - Auto-fix suggestions
    - Applied changes log
    """

    filename = _safe_str(session.get("fileName") or session.get("filename") or "file.edi")
    status = _safe_str(session.get("status") or "")
    session_id = _safe_str(session.get("_id") or session.get("id") or "")

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
        title="Validation + Fix Report",
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

    story = []
    story.append(Paragraph("Validation + Auto-Fix Report", title_style))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            f"Generated: {_safe_str(datetime.utcnow().isoformat())}",
            meta_style,
        )
    )
    story.append(Paragraph(f"Session ID: {session_id}", meta_style))
    story.append(Paragraph(f"File: {filename}", meta_style))
    if status:
        story.append(Paragraph(f"Status: {status}", meta_style))
    story.append(Spacer(1, 14))

    # Summary table
    story.append(Paragraph("Summary", h_style))
    summary_data = [
        ["Uploaded-file issues", str(len(original_issues))],
        ["Current validation issues", str(len(validation_issues))],
        ["Auto-fix suggestions", str(len(fix_suggestions))],
        ["Changes applied", str(len(changes_log))],
    ]
    summary_table = Table(summary_data, colWidths=[3.4 * inch, 2.2 * inch])
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

    # Issues (Uploaded-file)
    story.append(Spacer(1, 12))
    story.append(Paragraph("Uploaded-file Validation Issues", h_style))

    if not original_issues:
        story.append(Paragraph("No validation issues found.", small_style))
    else:
        issues_rows = [["ID", "Severity", "Segment", "Element", "Message"]]
        for err in original_issues[:250]:
            if not isinstance(err, dict):
                continue
            issues_rows.append(
                [
                    _compact_text(err.get("id"), 40),
                    _compact_text(err.get("severity"), 16),
                    _compact_text(err.get("segment"), 10),
                    _compact_text(err.get("field") or err.get("element"), 10),
                    _compact_text(err.get("message") or err.get("error") or err.get("description"), 120),
                ]
            )

        issues_table = Table(
            issues_rows,
            colWidths=[1.25 * inch, 0.75 * inch, 0.65 * inch, 0.65 * inch, 2.6 * inch],
            repeatRows=1,
        )
        issues_table.setStyle(
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
        story.append(issues_table)

        if len(original_issues) > 250:
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"(Truncated to first 250 issues)", meta_style))

    # Issues (Current)
    story.append(Spacer(1, 12))
    story.append(Paragraph("Current Validation Issues (After Fixes)", h_style))

    if not validation_issues:
        story.append(Paragraph("No current validation issues found.", small_style))
    else:
        issues_rows2 = [["ID", "Severity", "Segment", "Element", "Message"]]
        for err in validation_issues[:250]:
            if not isinstance(err, dict):
                continue
            issues_rows2.append(
                [
                    _compact_text(err.get("id"), 40),
                    _compact_text(err.get("severity"), 16),
                    _compact_text(err.get("segment"), 10),
                    _compact_text(err.get("field") or err.get("element"), 10),
                    _compact_text(err.get("message") or err.get("error") or err.get("description"), 120),
                ]
            )

        issues_table2 = Table(
            issues_rows2,
            colWidths=[1.25 * inch, 0.75 * inch, 0.65 * inch, 0.65 * inch, 2.6 * inch],
            repeatRows=1,
        )
        issues_table2.setStyle(
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
        story.append(issues_table2)

        if len(validation_issues) > 250:
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"(Truncated to first 250 issues)", meta_style))

    story.append(PageBreak())

    # Fix suggestions
    story.append(Paragraph("Fix Suggestions", h_style))
    if not fix_suggestions:
        story.append(Paragraph("No auto-fix suggestions available.", small_style))
    else:
        fixes_rows = [["Fix ID", "Type", "Confidence", "Auto", "Linked Error", "Target", "Suggested", "Status"]]
        for f in fix_suggestions[:250]:
            if not isinstance(f, dict):
                continue
            target = f"{_safe_str(f.get('segmentId') or f.get('segment'))} · {_safe_str(f.get('elementId') or f.get('element') or f.get('field'))}"
            fixes_rows.append(
                [
                    _compact_text(f.get("id"), 32),
                    _compact_text(f.get("fix_type"), 16),
                    _compact_text(f.get("confidence"), 8),
                    _compact_text(f.get("auto_apply"), 5),
                    _compact_text(f.get("errorId"), 40),
                    _compact_text(target, 40),
                    _compact_text(f.get("suggested"), 40),
                    _compact_text(f.get("status"), 12),
                ]
            )

        fixes_table = Table(
            fixes_rows,
            colWidths=[0.7 * inch, 0.8 * inch, 0.7 * inch, 0.45 * inch, 1.0 * inch, 0.85 * inch, 1.05 * inch, 0.55 * inch],
            repeatRows=1,
        )
        fixes_table.setStyle(
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
        story.append(fixes_table)
        if len(fix_suggestions) > 250:
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"(Truncated to first 250 fixes)", meta_style))

        # Include reasoning snippets (text) for the first few fixes
        reasoning_items = []
        for f in fix_suggestions[:12]:
            if not isinstance(f, dict):
                continue
            r = _safe_str(f.get("reasoning") or "").strip()
            if not r:
                continue
            reasoning_items.append(f"• {_safe_str(f.get('id'))}: {_compact_text(r, 220)}")
        if reasoning_items:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Fix Reasoning (sample)", h_style))
            story.append(Paragraph("<br/>".join(reasoning_items), small_style))

    story.append(Spacer(1, 14))
    story.append(Paragraph("Changes Log", h_style))
    if not changes_log:
        story.append(Paragraph("No changes applied yet.", small_style))
    else:
        changes_rows = [["Timestamp", "Target", "Old", "New"]]
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
                    _compact_text(ts_str, 28),
                    _compact_text(target, 30),
                    _compact_text(c.get("old"), 40),
                    _compact_text(c.get("new"), 40),
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

    # Appendix: EDI
    story.append(PageBreak())
    story.append(Paragraph("EDI Appendix", h_style))
    body = corrected_edi.strip() or raw_edi.strip()
    label = "Corrected EDI" if corrected_edi.strip() else "Uploaded Raw EDI"
    story.append(Paragraph(f"{label} (truncated)", meta_style))
    if not body:
        story.append(Paragraph("No EDI content available.", small_style))
    else:
        # Keep PDF size reasonable
        max_chars = 12000
        truncated = body[:max_chars]
        if len(body) > max_chars:
            truncated += "\n… (truncated)"
        pre = _escape_pre(truncated).replace("\n", "<br/>")
        story.append(Spacer(1, 8))
        story.append(Paragraph(f"<font name='Courier' size='8'>{pre}</font>", small_style))

    doc.build(story)
    return buf.getvalue()
