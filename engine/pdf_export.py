# engine/pdf_export.py

from __future__ import annotations

import io
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

# A4 at 300 DPI (approx); you can tweak if needed
PAGE_WIDTH = 2480
PAGE_HEIGHT = 3508

HEADER_HEIGHT = 380
MARGIN_X = 160
MARGIN_TOP = HEADER_HEIGHT + 140
COLUMN_GAP = 80

BRAND_BLUE = (7, 56, 99)       # dark blue header
LIGHT_GRAY = (245, 247, 250)   # subtle background if needed
TEXT_DARK = (20, 20, 20)


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Try a few common fonts so it works on Streamlit Cloud and locally.
    Fall back to the default PIL bitmap font if none are found.
    """
    preferred = [
        "DejaVuSans.ttf",
        "arial.ttf",
        "Helvetica.ttf",
    ]
    for name in preferred:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont,
               max_width: int) -> list[str]:
    """
    Simple word-wrap using draw.textlength (works on modern Pillow).
    Returns a list of lines that fit within max_width.
    """
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        test = (current + " " + word).strip()
        width = draw.textlength(test, font=font)
        if width <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def _draw_paragraph(draw: ImageDraw.ImageDraw,
                    text: str,
                    font: ImageFont.FreeTypeFont,
                    x: int,
                    y: int,
                    max_width: int,
                    line_spacing: int = 8) -> int:
    """
    Draw a multi-line paragraph and return the new y position after the text.
    """
    text = text.replace("\r", " ").strip()
    if not text:
        return y

    lines = _wrap_text(text, draw, font, max_width)
    for line in lines:
        draw.text((x, y), line, font=font, fill=TEXT_DARK)
        # estimate line height from textbbox
        bbox = draw.textbbox((x, y), line, font=font)
        line_height = bbox[3] - bbox[1]
        y += line_height + line_spacing

    return y


def _clean_markdown(text: str) -> str:
    """
    Remove the most obvious markdown markers so it looks nicer in PDF.
    """
    replacements = [
        ("**", ""),
        ("__", ""),
        ("### ", ""),
        ("## ", ""),
        ("# ", ""),
        ("\t", " "),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    # Normalise bullet markers
    text = text.replace("- ", "• ")
    text = text.replace("* ", "• ")

    return text.strip()


def _extract_title_from_ai(ai_brief: str) -> str:
    """
    Take the first line of the AI brief and convert it into a nice title.
    Example input:
        'Consulting Brief: Cultural Resistance Blocking Finance Transformation'
    Output (for Option B):
        'Bivenue Copilot – Cultural Resistance Blocking Finance Transformation'
    """
    if not ai_brief.strip():
        return "Bivenue Copilot – Finance Transformation Brief"

    first_line = ai_brief.strip().splitlines()[0]
    first_line = first_line.lstrip("#").strip()

    # If it starts with "Consulting Brief:", strip that label
    lower = first_line.lower()
    prefix = "consulting brief:"
    if lower.startswith(prefix):
        first_line = first_line[len(prefix):].strip()

    if not first_line:
        first_line = "Finance Transformation Brief"

    return f"Bivenue Copilot – {first_line}"


# -------------------------------------------------------------------------
# Main export function
# -------------------------------------------------------------------------

def create_consulting_brief_pdf(
    logo_path: Optional[str],
    domain: str,
    challenge: str,
    rule_based_summary: str,
    ai_brief: str,
    company_name: str,
    industry: str,
    revenue: Optional[str] = None,
    employees: Optional[str] = None,
) -> bytes:
    """
    Build a one-page consulting-style PDF (Gartner-like layout).
    Returns raw PDF bytes.
    """
    # 1) Canvas
    img = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = _load_font(90)
    font_subtitle = _load_font(52)
    font_heading = _load_font(54)
    font_body = _load_font(38)
    font_small = _load_font(34)

    # 2) Header bar
    draw.rectangle([0, 0, PAGE_WIDTH, HEADER_HEIGHT], fill=BRAND_BLUE)

    # Title (from AI brief, branded)
    title_text = _extract_title_from_ai(ai_brief)
    title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = MARGIN_X
    title_y = 110
    draw.text((title_x, title_y), title_text, font=font_title, fill="white")

    # Subtitle
    subtitle_text = "AI-generated Finance Transformation Consulting Brief"
    draw.text(
        (title_x, title_y + 120),
        subtitle_text,
        font=font_subtitle,
        fill="white",
    )

    # Optional logo (left side of header)
    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # Fit height ~160 px
            desired_h = 160
            ratio = desired_h / logo.height
            new_size = (int(logo.width * ratio), desired_h)
            logo = logo.resize(new_size, Image.LANCZOS)

            logo_x = PAGE_WIDTH - new_size[0] - MARGIN_X
            logo_y = (HEADER_HEIGHT - new_size[1]) // 2
            img.paste(logo, (logo_x, logo_y), mask=logo)
        except Exception:
            # If anything fails, we silently ignore the logo
            pass

    # 3) Company profile box (top-right, inside white area)
    box_w = 620
    box_h = 260
    box_x = PAGE_WIDTH - box_w - MARGIN_X
    box_y = HEADER_HEIGHT + 40

    draw.rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        outline=BRAND_BLUE,
        width=4,
        fill="white",
    )

    draw.text(
        (box_x + 32, box_y + 24),
        "Company Profile",
        font=font_heading,
        fill=BRAND_BLUE,
    )

    profile_y = box_y + 110
    draw.text((box_x + 32, profile_y), f"Name: {company_name}", font=font_small, fill=TEXT_DARK)
    profile_y += 52
    draw.text((box_x + 32, profile_y), f"Industry: {industry}", font=font_small, fill=TEXT_DARK)
    profile_y += 52

    if revenue:
        draw.text((box_x + 32, profile_y), f"Revenue: {revenue}", font=font_small, fill=TEXT_DARK)
        profile_y += 52
    if employees:
        draw.text((box_x + 32, profile_y), f"Employees: {employees}", font=font_small, fill=TEXT_DARK)

    # 4) Three-column layout
    # Available width under the header, excluding margins and gap
    total_width = PAGE_WIDTH - 2 * MARGIN_X - COLUMN_GAP * 2
    col_width = total_width // 3

    col1_x = MARGIN_X
    col2_x = col1_x + col_width + COLUMN_GAP
    col3_x = col2_x + col_width + COLUMN_GAP
    start_y = MARGIN_TOP

    # Column 1: Mission-critical priority
    heading_y = start_y
    draw.text(
        (col1_x, heading_y),
        "Mission-critical priority",
        font=font_heading,
        fill=BRAND_BLUE,
    )
    heading_y += 80

    mc_text = f"Mission-critical priority: {domain}\n\n{challenge}"
    mc_text = _clean_markdown(mc_text)
    _draw_paragraph(draw, mc_text, font_body, col1_x, heading_y, col_width)

    # Column 2: How Bivenue helped (rule-based summary)
    heading_y = start_y
    draw.text(
        (col2_x, heading_y),
        "How Bivenue helped",
        font=font_heading,
        fill=BRAND_BLUE,
    )
    heading_y += 80

    helped_text = _clean_markdown(rule_based_summary)
    _draw_paragraph(draw, helped_text, font_body, col2_x, heading_y, col_width)

    # Column 3: Outcome & AI deep-dive insights (AI brief)
    heading_y = start_y
    draw.text(
        (col3_x, heading_y),
        "Outcome & AI deep-dive insights",
        font=font_heading,
        fill=BRAND_BLUE,
    )
    heading_y += 80

    ai_text = _clean_markdown(ai_brief)
    _draw_paragraph(draw, ai_text, font_body, col3_x, heading_y, col_width)

    # Footer note
    footer_text = (
        "This brief was generated by Bivenue Copilot – an AI-assisted Finance Transformation Advisor."
    )
    footer_y = PAGE_HEIGHT - 160
    _draw_paragraph(
        draw,
        footer_text,
        font_small,
        MARGIN_X,
        footer_y,
        PAGE_WIDTH - 2 * MARGIN_X,
        line_spacing=4,
    )

    # 5) Convert to PDF bytes
    output = io.BytesIO()
    img.save(output, format="PDF")
    output.seek(0)
    return output.read()
