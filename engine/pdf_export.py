# engine/pdf_export.py

from __future__ import annotations

from io import BytesIO
from typing import Optional, List

import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    KeepTogether,
)


def _build_styles():
    styles = getSampleStyleSheet()

    # Base styles
    body = styles["BodyText"]
    body.fontName = "Helvetica"
    body.fontSize = 10
    body.leading = 13

    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=body,
            fontSize=9,
            leading=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#003366"),
            spaceBefore=12,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="MiniHeading",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#003366"),
            spaceBefore=4,
            spaceAfter=4,
        )
    )

    return styles


def _make_first_page_drawer(
    title: str,
    company_name: Optional[str],
    industry: Optional[str],
    revenue: Optional[str],
    employees: Optional[str],
    logo_path: Optional[str],
):
    """Create a closure used as reportlab's onFirstPage callback."""

    def first_page(canvas, doc):
        width, height = A4
        header_h = 60 * mm

        canvas.saveState()

        # Top blue band
        canvas.setFillColor(colors.HexColor("#003366"))
        canvas.rect(0, height - header_h, width, header_h, fill=1, stroke=0)

        # Logo (if available)
        if logo_path and os.path.exists(logo_path):
            logo_w = 35 * mm
            logo_h = 18 * mm
            x = 20 * mm
            y = height - header_h + header_h / 2 - logo_h / 2
            canvas.drawImage(
                logo_path,
                x,
                y,
                width=logo_w,
                height=logo_h,
                preserveAspectRatio=True,
                mask="auto",
            )

        # Main title
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 24)
        canvas.drawString(60 * mm, height - 25 * mm, "Bivenue Copilot")

        canvas.setFont("Helvetica", 11)
        canvas.drawString(60 * mm, height - 34 * mm, title)

        # Company profile box (right side)
        box_w = 70 * mm
        box_h = 40 * mm
        x = width - box_w - 20 * mm
        y = height - header_h + (header_h - box_h) / 2

        canvas.setFillColor(colors.white)
        canvas.roundRect(x, y, box_w, box_h, 4 * mm, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor("#d0d0d0"))
        canvas.roundRect(x, y, box_w, box_h, 4 * mm, fill=0, stroke=1)

        canvas.setFillColor(colors.HexColor("#003366"))
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(x + 8, y + box_h - 12, "Company Profile")

        canvas.setFillColor(colors.black)
        canvas.setFont("Helvetica", 9)

        line_y = y + box_h - 25
        canvas.drawString(x + 8, line_y, f"Name: {company_name or 'Client'}")
        line_y -= 12
        canvas.drawString(x + 8, line_y, f"Industry: {industry or 'N/A'}")
        if revenue:
            line_y -= 12
            canvas.drawString(x + 8, line_y, f"Revenue: {revenue}")
        if employees:
            line_y -= 12
            canvas.drawString(x + 8, line_y, f"Employees: {employees}")

        canvas.restoreState()

    return first_page


def _later_pages(canvas, doc):
    """Header/footer for pages 2+."""
    width, height = A4
    canvas.saveState()

    canvas.setFillColor(colors.HexColor("#003366"))
    canvas.setFont("Helvetica", 9)
    canvas.drawString(25 * mm, height - 15 * mm, "Bivenue Copilot – Finance Transformation Brief")
    canvas.drawRightString(width - 25 * mm, height - 15 * mm, f"Page {doc.page}")

    canvas.restoreState()


def _ai_brief_to_flowables(text: str, styles) -> List:
    """Turn the AI brief text into reportlab Paragraphs with light heading detection."""
    flows: List = []

    if not text:
        return flows

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flows.append(Spacer(1, 4 * mm))
            continue

        # Simple numbered heading detection ("1. Something")
        if line[0].isdigit() and (line[1:3] == ". " or line[1:3] == ".)"):
            flows.append(Paragraph(f"<b>{line}</b>", styles["SectionHeading"]))
        # Lines ending with ":" as mini headings
        elif line.endswith(":"):
            flows.append(Paragraph(f"<b>{line}</b>", styles["MiniHeading"]))
        else:
            flows.append(Paragraph(line, styles["BodyText"]))

    return flows


def create_consulting_brief_pdf(
    *,
    logo_path: Optional[str],
    domain: Optional[str],
    challenge: str,
    rule_based_summary: str,
    ai_brief: Optional[str],
    company_name: Optional[str] = "Client",
    industry: Optional[str] = "Finance",
    revenue: Optional[str] = None,
    employees: Optional[str] = None,
) -> bytes:
    """
    Build a BCG-style, multi-page consulting brief PDF.

    Parameters map directly from the app:
    - logo_path: path to the Bivenue logo (relative to the repo root).
    - domain: detected finance domain (Intercompany, R2R, etc.).
    - challenge: original user problem statement.
    - rule_based_summary: markdown/text with focus areas & actions.
    - ai_brief: long-form AI analysis (Consulting Brief: ...).
    """

    buffer = BytesIO()
    styles = _build_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=25 * mm,
        rightMargin=25 * mm,
        topMargin=30 * mm,
        bottomMargin=20 * mm,
    )

    story: list = []

    # -------- PAGE 1 CONTENT (below the hero band) -------- #

    # Leave vertical space so we don't overwrite the blue header bar
    story.append(Spacer(1, 75 * mm))

    # Three-column “Mission / How Bivenue helped / Outcome” grid
    mini = styles["MiniHeading"]
    body_small = styles["BodySmall"]

    mission_text = f"Mission-critical priority: {domain or 'Finance transformation'}"
    how_helped_text = rule_based_summary or "—"
    outcome_intro = (ai_brief or "").strip()
    if len(outcome_intro) > 650:
        outcome_intro = outcome_intro[:650].rsplit(" ", 1)[0] + "…"

    table_data = [
        [
            Paragraph("<b>Mission-critical priority</b>", mini),
            Paragraph("<b>How Bivenue helped</b>", mini),
            Paragraph("<b>Outcome & AI deep-dive insights</b>", mini),
        ],
        [
            Paragraph(mission_text, body_small),
            Paragraph(how_helped_text, body_small),
            Paragraph(outcome_intro or "AI analysis not available.", body_small),
        ],
    ]

    table = Table(
        table_data,
        colWidths=[60 * mm, 70 * mm, 60 * mm],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#d0d0d0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(KeepTogether(table))
    story.append(Spacer(1, 12 * mm))

    # Short note at bottom of page 1
    story.append(
        Paragraph(
            "This brief was generated by <b>Bivenue Copilot</b> – AI-assisted Finance Transformation Advisor.",
            styles["BodySmall"],
        )
    )

    # Move to detailed pages
    story.append(PageBreak())

    # -------- PAGES 2+ : FULL AI BRIEF -------- #

    story.append(Paragraph("Consulting Brief – Full Analysis", styles["SectionHeading"]))
    story.append(Spacer(1, 2 * mm))

    # Original challenge
    story.append(Paragraph("<b>Original challenge</b>", styles["MiniHeading"]))
    story.append(Paragraph(challenge, styles["BodyText"]))
    story.append(Spacer(1, 8 * mm))

    if ai_brief:
        # Convert AI narrative into nice paragraphs & headings
        flows = _ai_brief_to_flowables(ai_brief, styles)
        story.extend(flows)
    else:
        story.append(
            Paragraph(
                "AI analysis was not available for this case. Only the rule-based diagnostic is shown.",
                styles["BodyText"],
            )
        )

    # -------- Build document -------- #

    title = f"{domain or 'Finance'} Consulting Brief"

    first_page_cb = _make_first_page_drawer(
        title=title,
        company_name=company_name,
        industry=industry,
        revenue=revenue,
        employees=employees,
        logo_path=logo_path,
    )

    doc.build(story, onFirstPage=first_page_cb, onLaterPages=_later_pages)

    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value
