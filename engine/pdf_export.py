# engine/pdf_export.py

import io
import os
import textwrap
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

# ------------ Brand & Layout Settings ------------ #

PAGE_WIDTH, PAGE_HEIGHT = 1654, 2339  # A4-ish portrait
MARGIN_X = 80
DARK_BLUE = (4, 40, 80)
TEAL = (0, 199, 255)
TEXT_COLOR = (0, 0, 0)
TEXT_GREY = (70, 70, 70)
LIGHT_PANEL = (238, 244, 249)
WHITE = (255, 255, 255)


def _load_font(size: int = 14, bold: bool = False) -> ImageFont.FreeTypeFont:
    """
    Try loading DejaVu or Arial; fallback to default if not available.
    We avoid fancy font logic to stay compatible on Streamlit Cloud.
    """
    names = []
    if bold:
        names = ["DejaVuSans-Bold.ttf", "arialbd.ttf"]
    else:
        names = ["DejaVuSans.ttf", "arial.ttf"]

    for name in names:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue

    return ImageFont.load_default()


def _wrap_paragraph(text: str, width_chars: int) -> List[str]:
    """
    Simple word-wrapping based on character width. Robust and environment-safe.
    """
    if not text:
        return []
    cleaned = " ".join(text.split())
    return textwrap.wrap(cleaned, width=width_chars)


def _draw_block(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    title: str,
    body_lines: List[str],
) -> int:
    """
    Draw a section title + wrapped body text.
    Returns new y after drawing.
    """
    title_font = _load_font(20, bold=True)
    body_font = _load_font(14)

    # Title
    draw.text((x, y), title, font=title_font, fill=DARK_BLUE)
    y += 28

    # Accent line
    title_width = len(title) * 10  # rough estimate is fine here
    draw.line(
        [(x, y), (x + title_width, y)],
        fill=TEAL,
        width=3,
    )
    y += 10

    # Body
    line_height = 18
    for line in body_lines:
        draw.text((x, y), line, font=body_font, fill=TEXT_COLOR)
        y += line_height

    return y


def create_consulting_brief_pdf(
    domain: str,
    challenge: str,
    rule_based_summary: str,
    ai_brief: Optional[str],
    company_name: str = "Butterfield-style Client",
    industry: str = "Finance",
    revenue: Optional[str] = None,
    employees: Optional[str] = None,
) -> bytes:
    """
    Create a 1-page Bivenue-branded consulting brief as a PDF.
    """

    # --- Base canvas ---
    img = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), WHITE)
    draw = ImageDraw.Draw(img)

    # --- Header band (dark blue) ---
    header_h = 220
    draw.rectangle([0, 0, PAGE_WIDTH, header_h], fill=DARK_BLUE)

    # Curved teal accent (Bivenue style)
    # Big ellipse at bottom of header to give a curved line feel
    ellipse_height = 140
    draw.pieslice(
        [
            -200,
            header_h - ellipse_height // 2,
            PAGE_WIDTH + 200,
            header_h + ellipse_height,
        ],
        start=0,
        end=180,
        fill=None,
        outline=TEAL,
        width=6,
    )

    # --- Logo on left (if present) ---
    # We assume logo is engine/bivenue_logo.png, next to this file.
    logo_path = os.path.join(os.path.dirname(__file__), "bivenue_logo.png")
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            target_h = 120
            ratio = target_h / max(logo.height, 1)
            logo = logo.resize((int(logo.width * ratio), target_h))
            img.paste(logo, (MARGIN_X, 50), logo)
        except Exception:
            pass

    # --- Title in header ---
    title_font = _load_font(34, bold=True)
    subtitle_font = _load_font(18)

    title_text = "Bivenue Copilot"
    subtitle_text = f"{domain} Consulting Brief"

    draw.text(
        (MARGIN_X + 320, 70),
        title_text,
        font=title_font,
        fill=WHITE,
    )
    draw.text(
        (MARGIN_X + 320, 120),
        subtitle_text,
        font=subtitle_font,
        fill=WHITE,
    )

    # --- Company profile panel (top-right) ---
    panel_w = 420
    panel_h = 150
    panel_x0 = PAGE_WIDTH - MARGIN_X - panel_w
    panel_y0 = 40
    panel_x1 = panel_x0 + panel_w
    panel_y1 = panel_y0 + panel_h

    draw.rounded_rectangle(
        [panel_x0, panel_y0, panel_x1, panel_y1],
        radius=20,
        fill=LIGHT_PANEL,
    )

    panel_title_font = _load_font(16, bold=True)
    panel_body_font = _load_font(13)

    draw.text(
        (panel_x0 + 20, panel_y0 + 15),
        "Company Profile",
        font=panel_title_font,
        fill=DARK_BLUE,
    )

    info_y = panel_y0 + 50
    line_gap = 18

    def _panel_line(label: str, value: Optional[str]) -> None:
        nonlocal info_y
        if not value:
            return
        draw.text(
            (panel_x0 + 20, info_y),
            f"{label}: {value}",
            font=panel_body_font,
            fill=TEXT_COLOR,
        )
        info_y += line_gap

    _panel_line("Name", company_name)
    _panel_line("Industry", industry)
    _panel_line("Revenue", revenue)
    _panel_line("Employees", employees)

    # --- Columns layout ---
    y_start = header_h + 60
    available_width = PAGE_WIDTH - 2 * MARGIN_X
    gap = 30
    col_width = (available_width - 2 * gap) // 3

    col1_x = MARGIN_X
    col2_x = MARGIN_X + col_width + gap
    col3_x = MARGIN_X + 2 * (col_width + gap)

    # Column 1 – Mission-critical priority
    mission_text = f"{challenge}"
    mission_lines = _wrap_paragraph(mission_text, width_chars=60)
    _draw_block(draw, col1_x, y_start, "Mission-critical priority", mission_lines)

    # Column 2 – How Bivenue helped (rule-based)
    cleaned_summary = (
        rule_based_summary.replace("*", "").replace("#", "").strip()
        if rule_based_summary
        else ""
    )
    rb_lines = _wrap_paragraph(cleaned_summary, width_chars=60)
    _draw_block(draw, col2_x, y_start, "How Bivenue helped", rb_lines)

    # Column 3 – Outcome & AI deep-dive
    if not ai_brief:
        outcome_text = (
            "AI deep-dive insights were not available for this run. "
            "Please ensure the AI key is configured and try again."
        )
    else:
        # Strip a leading markdown heading like "# Intercompany Consulting Brief"
        stripped = ai_brief.strip()
        if stripped.startswith("#"):
            parts = stripped.splitlines()
            if len(parts) > 1:
                stripped = "\n".join(parts[1:])
        outcome_text = stripped

    outcome_lines = _wrap_paragraph(outcome_text, width_chars=65)
    _draw_block(draw, col3_x, y_start, "Outcome & AI deep-dive insights", outcome_lines)

    # --- Footer ---
    footer_text = (
        "This brief was generated by Bivenue Copilot – an AI-assisted Finance Transformation Advisor."
    )
    footer_font = _load_font(12)
    footer_y = PAGE_HEIGHT - 80
    draw.text((MARGIN_X, footer_y), footer_text, font=footer_font, fill=TEXT_GREY)

    # --- Convert to PDF ---
    buffer = io.BytesIO()
    img_rgb = img.convert("RGB")
    img_rgb.save(buffer, format="PDF")
    buffer.seek(0)
    return buffer.getvalue()
