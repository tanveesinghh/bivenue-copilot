import os
from io import BytesIO
from textwrap import shorten

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame


# --- Paths & Brand -----------------------------------------------------------------

BASE_DIR = os.path.dirname(__file__)
LOGO_PATH = os.path.join(BASE_DIR, "bivenue_logo.png")

BRAND_BLUE = colors.HexColor("#003366")   # dark blue
ACCENT_BLUE = colors.HexColor("#00c2ff")  # teal/cyan accent


# --- Helpers -----------------------------------------------------------------------


def _clean_ai_brief(ai_brief: str) -> str:
    """
    Remove duplicated heading like 'Intercompany Consulting Brief'
    when the AI already includes a title.
    """
    if not ai_brief:
        return ""

    # Normalize just for checking
    lower = ai_brief.lower().strip()
    if lower.startswith("intercompany consulting brief"):
        # Drop the first line (the heading) and keep the rest
        parts = ai_brief.splitlines()
        if len(parts) > 1:
            return "\n".join(parts[1:]).lstrip()

    return ai_brief


def _make_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="HeadingSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=BRAND_BLUE,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#555555"),
        )
    )

    styles.add(
        ParagraphStyle(
            name="Tiny",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=6,
            leading=7,
            textColor=colors.HexColor("#777777"),
        )
    )

    return styles


# --- Core export function ----------------------------------------------------------


def build_consulting_brief_pdf(
    problem: str,
    domain: str,
    rule_based_summary: str,
    ai_brief: str | None,
) -> BytesIO:
    """
    Create a Gartner-style single-page consulting brief PDF and return it as BytesIO.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    styles = _make_styles()

    # ------------------ HEADER BAND ------------------------------------------------
    header_height = 32 * mm
    c.setFillColor(BRAND_BLUE)
    c.rect(0, height - header_height, width, header_height, fill=1, stroke=0)

    # Logo on left
    try:
        logo_width = 35 * mm
        logo_height = 14 * mm
        c.drawImage(
            LOGO_PATH,
            15 * mm,
            height - header_height + (header_height - logo_height) / 2,
            width=logo_width,
            height=logo_height,
            preserveAspectRatio=True,
            mask="auto",
        )
    except Exception:
        # Fail silently if logo missing
        pass

    # Title text
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(60 * mm, height - 18 * mm, "Bivenue Copilot")

    c.setFont("Helvetica", 10)
    c.drawString(60 * mm, height - 24 * mm, "Intercompany Consulting Brief")

    # Thin accent line
    c.setFillColor(ACCENT_BLUE)
    c.rect(0, height - header_height - 1.5 * mm, width, 1.5 * mm, fill=1, stroke=0)

    # ------------------ COMPANY PROFILE BOX (top-right) ---------------------------
    profile_x = width - 65 * mm
    profile_y = height - header_height - 5 * mm
    profile_w = 55 * mm
    profile_h = 35 * mm

    c.setFillColor(colors.white)
    c.setStrokeColor(BRAND_BLUE)
    c.rect(profile_x, profile_y, profile_w, profile_h, fill=1, stroke=1)

    c.setFillColor(BRAND_BLUE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(profile_x + 4 * mm, profile_y + profile_h - 7 * mm, "Company Profile")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 7)
    # You can later make these dynamic; for now, generic placeholders
    c.drawString(profile_x + 4 * mm, profile_y + profile_h - 13 * mm, "Name: Bivenue-style Client")
    c.drawString(profile_x + 4 * mm, profile_y + profile_h - 19 * mm, f"Industry: Finance")
    c.drawString(profile_x + 4 * mm, profile_y + profile_h - 25 * mm, f"Domain: {domain}")

    # ------------------ MAIN 3-COLUMN LAYOUT --------------------------------------
    margin_x = 15 * mm
    top_y = height - header_height - 10 * mm
    bottom_y = 20 * mm
    column_gap = 8 * mm
    total_width = width - 2 * margin_x
    column_width = (total_width - 2 * column_gap) / 3

    # Column X positions
    col1_x = margin_x
    col2_x = margin_x + column_width + column_gap
    col3_x = margin_x + 2 * (column_width + column_gap)

    # ---------- Column 1: Mission-critical priority --------------------------------
    mission_story = shorten(problem.replace("\n", " "), width=600, placeholder="...")

    col1_flow = []
    col1_flow.append(Paragraph("Mission-critical priority", styles["HeadingSection"]))
    col1_flow.append(
        Paragraph("Mission-critical priority:", styles["Small"])
    )
    col1_flow.append(Paragraph(mission_story, styles["Body"]))

    col1_frame = Frame(
        col1_x,
        bottom_y,
        column_width,
        top_y - bottom_y,
        showBoundary=0,
    )
    col1_frame.addFromList(col1_flow, c)

    # ---------- Column 2: How Bivenue helped (rule-based) --------------------------
    rule_text = rule_based_summary.replace("##", "").replace("#", "")
    rule_text = rule_text.replace("*", "•")  # basic bullet formatting

    col2_flow = []
    col2_flow.append(Paragraph("How Bivenue helped", styles["HeadingSection"]))
    col2_flow.append(Paragraph("How Bivenue helped:", styles["Small"]))
    col2_flow.append(Paragraph(rule_text, styles["Body"]))

    col2_frame = Frame(
        col2_x,
        bottom_y,
        column_width,
        top_y - bottom_y,
        showBoundary=0,
    )
    col2_frame.addFromList(col2_flow, c)

    # ---------- Column 3: Outcome & AI deep-dive -----------------------------------
    cleaned_ai = _clean_ai_brief(ai_brief or "")
    if not cleaned_ai:
        cleaned_ai = "AI deep-dive insights will appear here once the copilot is connected and configured."

    cleaned_ai = cleaned_ai.replace("##", "").replace("#", "")
    cleaned_ai = cleaned_ai.replace("*", "•")

    col3_flow = []
    col3_flow.append(Paragraph("Outcome", styles["HeadingSection"]))
    col3_flow.append(Paragraph("Outcome & AI deep-dive insights:", styles["Small"]))
    col3_flow.append(Paragraph(cleaned_ai, styles["Body"]))

    col3_frame = Frame(
        col3_x,
        bottom_y,
        column_width,
        top_y - bottom_y,
        showBoundary=0,
    )
    col3_frame.addFromList(col3_flow, c)

    # ------------------ FOOTER NOTE -------------------------------------------------
    footer_text = (
        "This brief was generated by Bivenue Copilot – an AI-assisted Finance Transformation Advisor."
    )
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawString(margin_x, 12 * mm, footer_text)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
