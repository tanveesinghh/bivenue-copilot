from io import BytesIO
from textwrap import wrap

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


BRAND_BLUE = colors.HexColor("#003B73")   # dark blue
ACCENT_BLUE = colors.HexColor("#00B7FF")  # lighter accent


def _draw_wrapped_text(c, text, x, y, max_width, leading=12, font_name="Helvetica", font_size=9):
    """
    Helper to draw wrapped text and return the new y position.
    """
    c.setFont(font_name, font_size)
    if not text:
        return y

    # naive wrapping (works fine for our short briefs)
    words = text.replace("\r", " ").split("\n")
    lines = []
    for block in words:
        lines.extend(wrap(block, 120))  # adjust if needed

    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def create_consulting_brief_pdf(
    logo_path: str,
    domain: str,
    challenge: str,
    rule_based_summary: str,
    ai_brief: str,
    company_name: str = "Client",
    industry: str | None = None,
    revenue: str | None = None,
    employees: str | None = None,
) -> bytes:
    """
    Build a 1-page consulting brief PDF and return the bytes.
    Layout is inspired by Gartner-style one-pagers.
    """

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # -------------------------------------------------------
    # 1. Header band with logo + title
    # -------------------------------------------------------
    header_height = 40 * mm
    c.setFillColor(BRAND_BLUE)
    c.rect(0, height - header_height, width, header_height, fill=1, stroke=0)

    # Bivenue Copilot title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(25 * mm, height - 20 * mm, "Bivenue Copilot")

    c.setFont("Helvetica", 10)
    c.drawString(25 * mm, height - 26 * mm, "Intercompany Consulting Brief")

    # Logo on right (if file exists)
    try:
        logo = ImageReader(logo_path)
        logo_w = 25 * mm
        logo_h = 25 * mm
        c.drawImage(
            logo,
            width - logo_w - 15 * mm,
            height - logo_h - 12 * mm,
            width=logo_w,
            height=logo_h,
            mask="auto",
        )
    except Exception:
        # if logo fails, just ignore — don't break PDF
        pass

    # Thin accent line below header
    c.setFillColor(ACCENT_BLUE)
    c.rect(0, height - header_height - 2 * mm, width, 1.2 * mm, fill=1, stroke=0)

    # -------------------------------------------------------
    # 2. Company profile box (top-right)
    # -------------------------------------------------------
    right_col_x = width * 0.60
    box_y_top = height - header_height - 8 * mm
    box_width = width * 0.35
    box_height = 35 * mm

    c.setFillColor(colors.whitesmoke)
    c.roundRect(
        right_col_x,
        box_y_top - box_height,
        box_width,
        box_height,
        4 * mm,
        fill=1,
        stroke=0,
    )

    c.setFillColor(BRAND_BLUE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(right_col_x + 5 * mm, box_y_top - 7 * mm, "Company Profile")

    c.setFont("Helvetica", 8)
    y = box_y_top - 13 * mm
    c.setFillColor(colors.black)
    c.drawString(right_col_x + 5 * mm, y, f"Name: {company_name}")
    y -= 5 * mm
    if industry:
        c.drawString(right_col_x + 5 * mm, y, f"Industry: {industry}")
        y -= 5 * mm
    if revenue:
        c.drawString(right_col_x + 5 * mm, y, f"Revenue: {revenue}")
        y -= 5 * mm
    if employees:
        c.drawString(right_col_x + 5 * mm, y, f"Employees: {employees}")
        y -= 5 * mm

    # -------------------------------------------------------
    # 3. Left column – Mission-critical priority
    # -------------------------------------------------------
    margin_x = 20 * mm
    content_top = height - header_height - 15 * mm

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_x, content_top, "Mission-critical priority")

    # Accent underline
    c.setFillColor(ACCENT_BLUE)
    c.rect(margin_x, content_top - 3 * mm, 60 * mm, 0.8 * mm, fill=1, stroke=0)

    c.setFillColor(colors.black)
    y = content_top - 10 * mm
    c.setFont("Helvetica", 9)
    c.drawString(margin_x, y, "Mission-critical priority:")
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin_x, y, domain or "Finance Transformation")
    y -= 10 * mm

    # -------------------------------------------------------
    # 4. Middle column – How Bivenue helped (rule-based)
    # -------------------------------------------------------
    middle_x = width * 0.33
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(middle_x, content_top, "How Bivenue helped")

    c.setFillColor(ACCENT_BLUE)
    c.rect(middle_x, content_top - 3 * mm, 60 * mm, 0.8 * mm, fill=1, stroke=0)

    y_mid = content_top - 10 * mm
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    y_mid = _draw_wrapped_text(
        c,
        rule_based_summary or "",
        middle_x,
        y_mid,
        max_width=width * 0.27,
        leading=11,
    )

    # -------------------------------------------------------
    # 5. Right column – Outcome & AI deep dive
    # -------------------------------------------------------
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(right_col_x, content_top, "Outcome")

    c.setFillColor(ACCENT_BLUE)
    c.rect(right_col_x, content_top - 3 * mm, box_width, 0.8 * mm, fill=1, stroke=0)

    y_right = content_top - 10 * mm
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)

    # Title from AI brief
    y_right = _draw_wrapped_text(
        c,
        "Outcome & AI deep-dive insights:",
        right_col_x,
        y_right,
        max_width=box_width,
        leading=11,
        font_name="Helvetica-Bold",
        font_size=9,
    )
    y_right -= 2 * mm
    y_right = _draw_wrapped_text(
        c,
        ai_brief or "",
        right_col_x,
        y_right,
        max_width=box_width,
        leading=11,
        font_name="Helvetica",
        font_size=8,
    )

    # -------------------------------------------------------
    # 6. Footer note
    # -------------------------------------------------------
    c.setFont("Helvetica-Oblique", 7)
    c.setFillColor(colors.grey)
    footer_text = (
        "This brief was generated by Bivenue Copilot – AI-assisted Finance Transformation Advisor."
    )
    c.drawString(margin_x, 12 * mm, footer_text)

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
