from io import BytesIO
from textwrap import wrap
from typing import Optional

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# --- Brand colours (adjust if you like) ---

DARK_BLUE_HEX = "#002B5C"   # main header colour
ACCENT_HEX = "#00CFFF"      # curved-line / accent colour


def _hex_to_rgb01(hex_color: str):
    """Convert #RRGGBB -> (r, g, b) in 0–1 range for reportlab."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return r, g, b


def _draw_wrapped_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_name: str = "Helvetica",
    font_size: int = 9,
    leading: Optional[float] = None,
):
    """
    Simple text wrapper: draw multi-line text within max_width.
    Returns the final y-coordinate after drawing.
    """
    if leading is None:
        leading = font_size + 2

    c.setFont(font_name, font_size)

    # crude width estimate: assume ~0.5 * font_size per character
    avg_char_width = font_size * 0.5
    max_chars = int(max_width / avg_char_width)
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        lines.extend(wrap(paragraph, width=max_chars))

    for line in lines:
        c.drawString(x, y, line)
        y -= leading

    return y


def create_consulting_brief_pdf(
    *,
    logo_path: str,
    domain: str,
    challenge: str,
    rule_based_summary: str,
    ai_brief: str,
    company_name: str = "Client Name",
    industry: str = "Finance",
    revenue: Optional[str] = None,
    employees: Optional[str] = None,
) -> BytesIO:
    """
    Create a 1-page, branded PDF consulting brief.

    Layout A:
    - Top dark-blue banner with logo & Bivenue Copilot
    - Right-hand company info box
    - Three content boxes:
        1) Mission-critical priority
        2) How Bivenue helped
        3) Outcome
    """
    # --- Canvas setup (A4 landscape) ---
    page = landscape(A4)
    width, height = page
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=page)

    dark_r, dark_g, dark_b = _hex_to_rgb01(DARK_BLUE_HEX)
    accent_r, accent_g, accent_b = _hex_to_rgb01(ACCENT_HEX)

    # --- Header bar ---
    header_height = 3 * cm
    c.setFillColorRGB(dark_r, dark_g, dark_b)
    c.rect(0, height - header_height, width, header_height, fill=1, stroke=0)

    # Accent line below header (thin turquoise stripe)
    c.setFillColorRGB(accent_r, accent_g, accent_b)
    c.rect(0, height - header_height - 0.25 * cm, width, 0.25 * cm, fill=1, stroke=0)

    # --- Logo on the left ---
    try:
        logo = ImageReader(logo_path)
        logo_width = 3.2 * cm
        logo_height = 3.2 * cm
        c.drawImage(
            logo,
            1 * cm,
            height - header_height + (header_height - logo_height) / 2,
            width=logo_width,
            height=logo_height,
            preserveAspectRatio=True,
            mask="auto",
        )
    except Exception:
        # If logo can't be loaded, fail silently and continue.
        pass

    # --- Title text on header ---
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(5 * cm, height - 1.4 * cm, "Bivenue Copilot")

    c.setFont("Helvetica", 11)
    c.drawString(5 * cm, height - 2.2 * cm, f"{domain} Consulting Brief")

    # --- Company info box on right ---
    box_width = 7 * cm
    box_height = header_height - 0.8 * cm
    box_x = width - box_width - 1 * cm
    box_y = height - header_height + 0.4 * cm

    c.setFillColorRGB(1, 1, 1)
    c.roundRect(box_x, box_y, box_width, box_height, 0.4 * cm, fill=1, stroke=0)

    c.setFillColorRGB(dark_r, dark_g, dark_b)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(box_x + 0.4 * cm, box_y + box_height - 0.7 * cm, "Company Profile")

    c.setFont("Helvetica", 8)
    y_ci = box_y + box_height - 1.4 * cm
    info_lines = [
        f"Name: {company_name}",
        f"Industry: {industry}",
    ]
    if revenue:
        info_lines.append(f"Revenue: {revenue}")
    if employees:
        info_lines.append(f"Employees: {employees}")

    for line in info_lines:
        c.drawString(box_x + 0.4 * cm, y_ci, line)
        y_ci -= 0.45 * cm

    # --- Main content area ---
    margin = 1.5 * cm
    content_top = height - header_height - 1.5 * cm
    content_bottom = 1.8 * cm

    # Define three columns / boxes
    total_width = width - 2 * margin
    col_width = (total_width - 2 * 0.8 * cm) / 3  # 0.8cm gap between columns

    # Shared style
    box_height_main = content_top - content_bottom

    def draw_box(x, title, body):
        """Draw a white box with title and body text."""
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(x, content_bottom, col_width, box_height_main, 0.4 * cm, fill=1, stroke=0)

        # small accent line under title
        inner_margin_x = x + 0.5 * cm
        inner_top_y = content_top - 0.6 * cm

        c.setFillColorRGB(dark_r, dark_g, dark_b)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(inner_margin_x, inner_top_y, title)

        c.setFillColorRGB(accent_r, accent_g, accent_b)
        c.rect(inner_margin_x, inner_top_y - 0.3 * cm, col_width - 1 * cm, 0.08 * cm, fill=1, stroke=0)

        # body text
        c.setFillColor(colors.black)
        body_y_start = inner_top_y - 0.8 * cm
        _draw_wrapped_text(
            c,
            body.strip(),
            inner_margin_x,
            body_y_start,
            max_width=col_width - 1 * cm,
            font_name="Helvetica",
            font_size=8.5,
            leading=11,
        )

    # Prepare texts for each box
    mission_text = (
        "Mission-critical priority:\n\n"
        f"{challenge.strip()}"
    )

    how_text = (
        "How Bivenue helped:\n\n"
        f"{rule_based_summary.strip()}"
    )

    outcome_text = (
        "Outcome & AI deep-dive insights:\n\n"
        f"{ai_brief.strip()}"
    )

    # Draw the three boxes
    x1 = margin
    x2 = margin + col_width + 0.8 * cm
    x3 = margin + 2 * (col_width + 0.8 * cm)

    draw_box(x1, "Mission-critical priority", mission_text)
    draw_box(x2, "How Bivenue helped", how_text)
    draw_box(x3, "Outcome", outcome_text)

    # --- Footer ---
    c.setFillColorRGB(dark_r, dark_g, dark_b)
    c.setFont("Helvetica-Oblique", 7)
    footer_text = "This brief was generated by Bivenue Copilot – AI-assisted Finance Transformation Advisor."
    c.drawString(margin, 0.9 * cm, footer_text)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf
