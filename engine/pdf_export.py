import io
import os
import textwrap
from typing import List, Tuple, Optional

from PIL import Image, ImageDraw, ImageFont

# --- Basic page + brand settings --- #

PAGE_WIDTH, PAGE_HEIGHT = 1654, 2339  # big vertical page
MARGIN = 80

DARK_BLUE = (8, 54, 94)
TEAL = (0, 199, 255)
TEXT_COLOR = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_PANEL = (238, 244, 249)


def _load_font(size: int = 14, bold: bool = False) -> ImageFont.FreeTypeFont:
    """
    Try DejaVu fonts if available; otherwise fall back to the default bitmap font.
    We avoid using any methods that aren't widely supported.
    """
    try:
        if bold:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _wrap_paragraph(text: str, width_chars: int = 90) -> List[str]:
    """
    Simple, robust word-wrapping based on a fixed character width.
    We don't rely on font metrics; this avoids AttributeError issues.
    """
    if not text:
        return []
    # Replace hard newlines with spaces, then wrap
    cleaned = " ".join(text.split())
    return textwrap.wrap(cleaned, width=width_chars)


def _draw_block(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    title: str,
    body_lines: List[str],
    title_color: Tuple[int, int, int] = DARK_BLUE,
    body_color: Tuple[int, int, int] = TEXT_COLOR,
) -> int:
    """
    Draws a block with a heading and multi-line body text.
    Returns the new y position after drawing.
    """
    title_font = _load_font(20, bold=True)
    body_font = _load_font(14)

    # Title
    draw.text((x, y), title, font=title_font, fill=title_color)
    y += 30

    # Body
    line_height = 18
    for line in body_lines:
        draw.text((x, y), line, font=body_font, fill=body_color)
        y += line_height

    return y


def create_consulting_brief_pdf(
    logo_path: Optional[str],
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
    Create a 1-page consulting brief styled in a Gartner-like layout.

    Returns raw PDF bytes that Streamlit can offer with st.download_button.
    """

    # --- Create base canvas --- #
    img = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), WHITE)
    draw = ImageDraw.Draw(img)

    # --- Header bar --- #
    header_height = 220
    draw.rectangle([0, 0, PAGE_WIDTH, header_height], fill=DARK_BLUE)

    # Optional logo (left side)
    if logo_path:
        try:
            # If logo_path is relative, resolve it relative to this file
            if not os.path.isabs(logo_path):
                base_dir = os.path.dirname(__file__)
                logo_path_abs = os.path.join(base_dir, logo_path)
            else:
                logo_path_abs = logo_path

            logo = Image.open(logo_path_abs).convert("RGBA")
            target_h = 120
            ratio = target_h / max(logo.height, 1)
            logo = logo.resize((int(logo.width * ratio), target_h))
            img.paste(logo, (MARGIN, 40), logo)
        except Exception:
            # If anything fails with the logo, just skip it
            pass

    # Header text (centre-ish)
    title_font = _load_font(34, bold=True)
    subtitle_font = _load_font(18)
    title_x = MARGIN + 320
    draw.text((title_x, 70), "Bivenue Copilot", font=title_font, fill=WHITE)
    draw.text(
        (title_x, 120),
        "Intercompany Consulting Brief",
        font=subtitle_font,
        fill=WHITE,
    )

    # Company profile panel on the right
    panel_w = 360
    panel_x0 = PAGE_WIDTH - MARGIN - panel_w
    panel_y0 = 40
    panel_y1 = header_height - 40
    draw.rectangle([panel_x0, panel_y0, panel_x0 + panel_w, panel_y1], fill=LIGHT_PANEL)

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

    # --- Three-column layout below header --- #
    y_start = header_height + 50
    available_width = PAGE_WIDTH - 2 * MARGIN
    gap = 30
    col_width = (available_width - 2 * gap) // 3

    col1_x = MARGIN
    col2_x = MARGIN + col_width + gap
    col3_x = MARGIN + 2 * (col_width + gap)

    # Column 1 – Mission-critical priority
    mission_lines = _wrap_paragraph(
        f"Mission-critical priority:\n{domain or 'Intercompany'}",
        width_chars=55,
    )
    mission_y = _draw_block(draw, col1_x, y_start, "Mission-critical priority", mission_lines)

    # Column 2 – How Bivenue helped (rule-based summary)
    rb_lines = _wrap_paragraph(rule_based_summary or "", width_chars=55)
    _draw_block(draw, col2_x, y_start, "How Bivenue helped", rb_lines)

    # Column 3 – Outcome & AI deep-dive
    if ai_brief:
        outcome_text = ai_brief
    else:
        outcome_text = (
            "AI deep-dive insights were not available for this run. "
            "Please ensure the AI key is configured and try again."
        )
    outcome_lines = _wrap_paragraph(outcome_text, width_chars=65)
    _draw_block(draw, col3_x, y_start, "Outcome & AI deep-dive insights", outcome_lines)

    # --- Footer --- #
    footer_text = (
        "This brief was generated by Bivenue Copilot – an AI-assisted Finance "
        "Transformation Advisor."
    )
    footer_font = _load_font(11)
    footer_y = PAGE_HEIGHT - 60
    draw.text((MARGIN, footer_y), footer_text, font=footer_font, fill=DARK_BLUE)

    # --- Convert to PDF bytes --- #
    buffer = io.BytesIO()
    rgb = img.convert("RGB")
    rgb.save(buffer, format="PDF")
    buffer.seek(0)
    return buffer.getvalue()
