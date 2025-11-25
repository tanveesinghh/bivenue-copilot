import io
from typing import Tuple, Optional

from PIL import Image, ImageDraw, ImageFont

# --- Brand & layout constants -------------------------------------------------

DARK_BLUE = "#003366"
ACCENT_BLUE = "#00bcd4"
TEXT_BLACK = "#000000"
TEXT_GREY = "#555555"
PAGE_WIDTH, PAGE_HEIGHT = 2480, 3508  # A4 at 300 dpi

MARGIN_X = 180
MARGIN_TOP = 260
COLUMN_GAP = 80


# --- Font helpers -------------------------------------------------------------


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Try to load a decent TTF font. If not available in the environment,
    gracefully fall back to Pillow's default bitmap font.
    """
    # You can change this to another common font if you prefer.
    for name in ["DejaVuSans.ttf", "arial.ttf", "Helvetica.ttf"]:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            continue

    # Fallback
    return ImageFont.load_default()


def _measure_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
) -> Tuple[int, int]:
    """
    Measure text size using textbbox (works on newer Pillow versions).
    Returns (width, height).
    """
    if not text:
        return 0, 0

    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> str:
    """
    Very simple word-wrap helper: returns text with '\n' inserted so that
    each line is <= max_width pixels (approx).
    """
    words = text.split()
    if not words:
        return ""

    lines = []
    current = words[0]

    for word in words[1:]:
        candidate = current + " " + word
        w_width, _ = _measure_text(draw, candidate, font)
        if w_width <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return "\n".join(lines)


def _draw_paragraph(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    x: int,
    y: int,
    max_width: int,
    line_spacing: int = 6,
    fill: str = TEXT_BLACK,
) -> int:
    """
    Draw a multi-line paragraph (with wrapping) starting at (x, y).
    Returns the new y position just after the paragraph.
    """
    wrapped = _wrap_text(draw, text, font, max_width)
    for line in wrapped.split("\n"):
        draw.text((x, y), line, font=font, fill=fill)
        _, h = _measure_text(draw, line, font)
        y += h + line_spacing
    return y


# --- Main export function -----------------------------------------------------


def create_consulting_brief_pdf(
    logo_path: Optional[str],
    domain: str,
    challenge: str,
    rule_based_summary: str,
    ai_brief: Optional[str],
    company_name: str,
    industry: str,
    revenue: Optional[str] = None,
    employees: Optional[str] = None,
) -> bytes:
    """
    Build a single-page consulting brief PDF with Bivenue branding.

    Returns: raw PDF bytes suitable for st.download_button(data=...).
    """

    # Base "page" as an RGB image we will save as PDF
    img = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
    draw = ImageDraw.Draw(img)

    # Load fonts
    title_font = _load_font(80)
    subtitle_font = _load_font(40)
    heading_font = _load_font(46)
    label_font = _load_font(32)
    body_font = _load_font(32)
    tiny_font = _load_font(20)

    # --- Top bar ----------------------------------------------------------------
    draw.rectangle(
        [(0, 0), (PAGE_WIDTH, 220)],
        fill=DARK_BLUE,
    )

    # Logo (left)
    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # Scale logo to fit nicely in the top bar
            target_height = 140
            ratio = target_height / logo.height
            new_size = (int(logo.width * ratio), target_height)
            logo = logo.resize(new_size, Image.LANCZOS)

            logo_x = MARGIN_X
            logo_y = 40
            img.paste(logo, (logo_x, logo_y), logo)
        except Exception:
            # If we can't load logo, just skip
            pass

    # Title (centre-ish)
    title_text = "Bivenue Copilot"
    subtitle_text = "Intercompany Consulting Brief"

    _, title_h = _measure_text(draw, title_text, title_font)
    _, subtitle_h = _measure_text(draw, subtitle_text, subtitle_font)

    center_x = PAGE_WIDTH // 2
    title_w, _ = _measure_text(draw, title_text, title_font)
    subtitle_w, _ = _measure_text(draw, subtitle_text, subtitle_font)

    draw.text(
        (center_x - title_w // 2, 60),
        title_text,
        font=title_font,
        fill="white",
    )
    draw.text(
        (center_x - subtitle_w // 2, 60 + title_h + 10),
        subtitle_text,
        font=subtitle_font,
        fill="white",
    )

    # Company profile box (top-right)
    box_width = 650
    box_height = 260
    box_x1 = PAGE_WIDTH - MARGIN_X - box_width
    box_y1 = 40
    box_x2 = box_x1 + box_width
    box_y2 = box_y1 + box_height

    draw.rounded_rectangle(
        [box_x1, box_y1, box_x2, box_y2],
        radius=30,
        fill="white",
        outline=None,
    )

    prof_title = "Company Profile"
    draw.text(
        (box_x1 + 40, box_y1 + 30),
        prof_title,
        font=heading_font,
        fill=DARK_BLUE,
    )

    info_y = box_y1 + 110
    info_x = box_x1 + 40

    def _line(label: str, value: Optional[str]):
        nonlocal info_y
        if value is None:
            return
        draw.text(
            (info_x, info_y),
            f"{label}: {value}",
            font=label_font,
            fill=TEXT_BLACK,
        )
        info_y += 46

    _line("Name", company_name)
    _line("Industry", industry)
    _line("Revenue", revenue)
    _line("Employees", employees)

    # --- Body columns ----------------------------------------------------------

    # Column widths (three columns)
    total_body_width = PAGE_WIDTH - 2 * MARGIN_X
    col_width = (total_body_width - 2 * COLUMN_GAP) // 3

    col1_x = MARGIN_X
    col2_x = col1_x + col_width + COLUMN_GAP
    col3_x = col2_x + col_width + COLUMN_GAP

    body_top_y = MARGIN_TOP

    # --- Column 1: Mission-critical priority -----------------------------------

    # Section heading
    draw.text(
        (col1_x, body_top_y),
        "Mission-critical priority",
        font=heading_font,
        fill=TEXT_BLACK,
    )
    # Accent line
    heading_w, heading_h = _measure_text(draw, "Mission-critical priority", heading_font)
    draw.line(
        [(col1_x, body_top_y + heading_h + 8), (col1_x + heading_w, body_top_y + heading_h + 8)],
        fill=ACCENT_BLUE,
        width=6,
    )

    y = body_top_y + heading_h + 30
    draw.text(
        (col1_x, y),
        "Mission-critical priority:",
        font=label_font,
        fill=TEXT_GREY,
    )
    y += 50

    # Use the original challenge as the mission-critical description
    y = _draw_paragraph(
        draw,
        challenge,
        body_font,
        x=col1_x,
        y=y,
        max_width=col_width,
        line_spacing=8,
        fill=TEXT_BLACK,
    )

    # --- Column 2: How Bivenue helped -----------------------------------------

    draw.text(
        (col2_x, body_top_y),
        "How Bivenue helped",
        font=heading_font,
        fill=TEXT_BLACK,
    )
    heading_w2, heading_h2 = _measure_text(draw, "How Bivenue helped", heading_font)
    draw.line(
        [(col2_x, body_top_y + heading_h2 + 8), (col2_x + heading_w2, body_top_y + heading_h2 + 8)],
        fill=ACCENT_BLUE,
        width=6,
    )

    y2 = body_top_y + heading_h2 + 30
    draw.text(
        (col2_x, y2),
        "How Bivenue helped:",
        font=label_font,
        fill=TEXT_GREY,
    )
    y2 += 50

    # The rule-based summary can be long markdown; we strip bullet markers
    cleaned_summary = (
        rule_based_summary.replace("*", "").replace("-", "").replace("#", "").strip()
    )

    y2 = _draw_paragraph(
        draw,
        cleaned_summary,
        body_font,
        x=col2_x,
        y=y2,
        max_width=col_width,
        line_spacing=8,
        fill=TEXT_BLACK,
    )

    # --- Column 3: AI deep-dive / Outcome --------------------------------------

    draw.text(
        (col3_x, body_top_y),
        "Outcome",
        font=heading_font,
        fill=TEXT_BLACK,
    )
    heading_w3, heading_h3 = _measure_text(draw, "Outcome", heading_font)
    draw.line(
        [(col3_x, body_top_y + heading_h3 + 8), (col3_x + heading_w3, body_top_y + heading_h3 + 8)],
        fill=ACCENT_BLUE,
        width=6,
    )

    y3 = body_top_y + heading_h3 + 30

    draw.text(
        (col3_x, y3),
        "Outcome & AI deep-dive insights:",
        font=label_font,
        fill=TEXT_GREY,
    )
    y3 += 50

    if not ai_brief:
        ai_brief = "AI analysis was not available for this case."

    cleaned_ai = ai_brief.strip()

    # Wrap & draw the AI analysis
    y3 = _draw_paragraph(
        draw,
        cleaned_ai,
        body_font,
        x=col3_x,
        y=y3,
        max_width=col_width,
        line_spacing=8,
        fill=TEXT_BLACK,
    )

    # --- Footer ----------------------------------------------------------------

    footer_text = (
        "This brief was generated by Bivenue Copilot – AI-assisted Finance Transformation Advisor."
    )
    footer_w, footer_h = _measure_text(draw, footer_text, tiny_font)
    footer_x = MARGIN_X
    footer_y = PAGE_HEIGHT - 200

    draw.text(
        (footer_x, footer_y),
        footer_text,
        font=tiny_font,
        fill=TEXT_GREY,
    )

    # --- Export to PDF bytes ---------------------------------------------------

    output = io.BytesIO()
    # Pillow can save a single-page PDF directly from an RGB image
    img.save(output, format="PDF", resolution=300.0)
    pdf_bytes = output.getvalue()
    output.close()

    return pdf_bytes
