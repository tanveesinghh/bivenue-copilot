# engine/pdf_export.py

from __future__ import annotations

import io
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, Paragraph


DARK_BLUE = colors.HexColor("#003366")
ACCENT_BLUE = colors.HexColor("#00B4FF")


def _make_styles():
    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.white,
        alignment=TA_LEFT,
    )

    subtitle = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=12,
        textColor=colors.white,
        alignment=TA_LEFT,
    )

    h4 = ParagraphStyle(
        "H4",
        parent=styles["Heading4"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=DARK_BLUE,
        spaceAfter=4,
    )

    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        textColor=colors.black,
        alignment=TA_LEFT,
    )

    footer = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7,
        leading=9,
        textColor=DARK_BLUE,
        alignment=TA_LEFT,
    )

    return {"title": title, "subtitle": subtitle, "h4": h4, "body": body, "footer": footer}


def build_brief_pdf(
    *,
    challenge: str,
    domain: str,
    rule_summary: str,
    ai_brief: str,
    client_name: str = "Butterfield-style Client",
    industry: str = "Finance",
    logo_path: str = "assets/bivenue_logo.png",
) -> bytes:
    """
    Build a single-page consulting brief PDF in Bivenue style.
    Returns the PDF bytes so Streamlit can offer it as download.
    """

    styles = _make_styles()
    buffer = io.BytesIO()

    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- HEADER BAND ---------------------------------------------------------
    header_h = 3 * cm
    c.setFillColor(DARK_BLUE)
    c.rect(0, height - header_h, width, header_h, fill=1, stroke=0)

    # logo (optional)
    logo_file = Path(logo_path)
    if logo_file.is_file():
        try:
            # small logo on left
            c.drawImage(
                str(logo_file),
                1 * cm,
                height - header_h + 0.5 * cm,
                width=3 * cm,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            # if logo fails, we just skip it
            pass

    # title + subtitle
    title_x = 5 * cm
    title_y = height - 1.2 * cm
    Paragraph("Bivenue Copilot", styles["title"]).wrapOn(c, width - title_x - 1 * cm, 20)
    Paragraph("Intercompany Consulting Brief", styles["subtitle"]).wrapOn(
        c, width - title_x - 1 * cm, 20
    )

    Paragraph("Bivenue Copilot", styles["title"]).drawOn(
        c, title_x, height - 1.4 * cm
    )
    Paragraph("Intercompany Consulting Brief", styles["subtitle"]).drawOn(
        c, title_x, height - 2.1 * cm
    )

    # thin accent line
    c.setFillColor(ACCENT_BLUE)
    c.rect(0, height - header_h - 0.15 * cm, width, 0.15 * cm, fill=1, stroke=0)

    # --- COMPANY PROFILE CARD (TOP RIGHT) -----------------------------------
    card_w = 6 * cm
    card_h = 3.5 * cm
    card_x = width - card_w - 1 * cm
    card_y = height - header_h - card_h + 0.6 * cm

    c.setFillColor(colors.white)
    c.roundRect(card_x, card_y, card_w, card_h, radius=0.3 * cm, fill=1, stroke=1)

    c.setFillColor(DARK_BLUE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(card_x + 0.5 * cm, card_y + card_h - 0.9 * cm, "Company Profile")

    c.setFont("Helvetica", 8)
    c.drawString(card_x + 0.5 * cm, card_y + card_h - 1.7 * cm, f"Name: {client_name}")
    c.drawString(card_x + 0.5 * cm, card_y + card_h - 2.4 * cm, f"Industry: {industry}")
    c.drawString(card_x + 0.5 * cm, card_y + card_h - 3.1 * cm, f"Domain: {domain}")

    # --- MAIN BODY: 3 COLUMNS -----------------------------------------------
    top_y = height - header_h - 1.2 * cm
    bottom_margin = 2.2 * cm
    available_h = top_y - bottom_margin

    col_gap = 0.7 * cm
    col_w = (width - 2 * cm - 2 * col_gap) / 3.0

    frame1 = Frame(
        1 * cm,
        bottom_margin,
        col_w,
        available_h,
        showBoundary=0,
    )
    frame2 = Frame(
        1 * cm + col_w + col_gap,
        bottom_margin,
        col_w,
        available_h,
        showBoundary=0,
    )
    frame3 = Frame(
        1 * cm + 2 * (col_w + col_gap),
        bottom_margin,
        col_w,
        available_h,
        showBoundary=0,
    )

    # Left column — Mission-critical priority
    mission_story = [
        Paragraph("Mission-critical priority", styles["h4"]),
        Paragraph(challenge.replace("\n", "<br/>"), styles["body"]),
    ]

    # Middle column — How Bivenue helped
    how_story = [
        Paragraph("How Bivenue helped", styles["h4"]),
        Paragraph(rule_summary.replace("\n", "<br/>"), styles["body"]),
    ]

    # Right column — Outcome (AI brief)
    outcome_story = [
        Paragraph("Outcome", styles["h4"]),
        Paragraph(ai_brief.replace("\n", "<br/>"), styles["body"]),
    ]

    frame1.addFromList(mission_story, c)
    frame2.addFromList(how_story, c)
    frame3.addFromList(outcome_story, c)

    # --- FOOTER --------------------------------------------------------------
    footer_text = (
        "This brief was generated by Bivenue Copilot – AI-assisted Finance "
        "Transformation Advisor."
    )
    Paragraph(footer_text, styles["footer"]).wrapOn(c, width - 2 * cm, 30)
    Paragraph(footer_text, styles["footer"]).drawOn(c, 1 * cm, 1.1 * cm)

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
