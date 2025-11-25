# engine/pdf_export.py

from io import BytesIO
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


# Try to load fonts that look a bit more “consulting deck” style.
# If these fail on Streamlit Cloud, Pillow will fall back to a default font.
def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    try:
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Simple word-wrap helper."""
    words = text.split()
    lines: list[str] = []
    current = ""

    for w in words:
        test = (current + " " + w).strip()
        w_width, _ = draw.textsize(test, font=font)
        if w_width <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def _draw_paragraph(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    width: int,
    font: ImageFont.ImageFont,
    fill: str = "black",
    line_spacing: int = 4,
) -> int:
    """
    Draws a multi-line paragraph and returns the new y position
    (just after the last line).
    """
    for line in _wrap_text(text, font, width, draw):
        draw.text((x, y), line, font=font, fill=fill)
        _, h = draw.textsize(line, font=font)
        y += h + line_spacing
    return y


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
    Generate a 1-page branded PDF in a Gartner-style layout.

    - Dark-blue header band
    - Logo + title on the left
    - Company profile card on the right
    - Three columns: Mission, How Bivenue helped, Outcome (AI brief)
    """

    # --- Page setup (A4-ish, landscape) ---
    width, height = 1754, 1240  # ~A4 landscape
    bg_color = "white"
    header_height = 170
    brand_blue = "#003B73"  # dark blue
    accent_blue = "#00B4FF"

    image = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(image)

    # --- Fonts ---
    title_font = _load_font(40, bold=True)
    subtitle_font = _load_font(22)
    section_title_font = _load_font(24, bold=True)
    body_font = _load_font(18)
    small_font = _load_font(14)

    # --- Header band ---
    draw.rectangle([(0, 0), (width, header_height)], fill=brand_blue)

    # --- Logo on left side of header ---
    x_logo = 40
    y_logo = 25
    logo_max_h = 90
    logo_max_w = 260

    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # scale down to fit box
            lw, lh = logo.size
            scale = min(logo_max_w / lw, logo_max_h / lh, 1.0)
            new_size = (int(lw * scale), int(lh * scale))
            logo = logo.resize(new_size, Image.LANCZOS)
            image.paste(logo, (x_logo, y_logo), logo)
        except Exception:
            # If logo fails to load we just skip it
            pass

    # --- Title + subtitle in header ---
    title_x = x_logo + logo_max_w + 30
    title_y = 45
    draw.text((title_x, title_y), "Bivenue Copilot", font=title_font, fill="white")
    subtitle_y = title_y + 50
    draw.text(
        (title_x, subtitle_y),
        f"{domain} Consulting Brief",
        font=subtitle_font,
        fill="white",
    )

    # --- Company profile card (right in header) ---
    card_width = 380
    card_height = header_height - 40
    card_x = width - card_width - 30
    card_y = 20

    draw.rounded_rectangle(
        [(card_x, card_y), (card_x + card_width, card_y + card_height)],
        radius=16,
        fill="white",
    )

    cp_title_y = card_y + 16
    draw.text((card_x + 20, cp_title_y), "Company Profile", font=section_title_font, fill=brand_blue)

    info_y = cp_title_y + 40
    info_y = _draw_paragraph(
        draw,
        f"Name: {company_name}",
        card_x + 20,
        info_y,
        card_width - 40,
        body_font,
        fill="black",
    )
    info_y = _draw_paragraph(
        draw,
        f"Industry: {industry}",
        card_x + 20,
        info_y,
        card_width - 40,
        body_font,
        fill="black",
    )
    if revenue:
        info_y = _draw_paragraph(
            draw,
            f"Revenue: {revenue}",
            card_x + 20,
            info_y,
            card_width - 40,
            body_font,
            fill="black",
        )
    if employees:
        _ = _draw_paragraph(
            draw,
            f"Employees: {employees}",
            card_x + 20,
            info_y,
            card_width - 40,
            body_font,
            fill="black",
        )

    # --- Thin accent line under header ---
    draw.rectangle([(0, header_height), (width, header_height + 6)], fill=accent_blue)

    # --- Column layout below header ---
    top = header_height + 30
    margin_x = 40
    usable_width = width - 2 * margin_x
    col_gap = 40
    col_width = int((usable_width - 2 * col_gap) / 3)

    col1_x = margin_x
    col2_x = col1_x + col_width + col_gap
    col3_x = col2_x + col_width + col_gap

    # --- Column 1: Mission-critical priority ---
    y1 = top
    draw.text((col1_x, y1), "Mission-critical priority", font=section_title_font, fill=brand_blue)
    y1 += 32
    # accent line
    draw.line([(col1_x, y1), (col1_x + col_width, y1)], fill=accent_blue, width=4)
    y1 += 16

    mission_text = f"Mission-critical priority:\n{domain}"
    y1 = _draw_paragraph(draw, mission_text, col1_x, y1, col_width, body_font)

    # --- Column 2: How Bivenue helped ---
    y2 = top
    draw.text((col2_x, y2), "How Bivenue helped", font=section_title_font, fill=brand_blue)
    y2 += 32
    draw.line([(col2_x, y2), (col2_x + col_width, y2)], fill=accent_blue, width=4)
    y2 += 16

    # Re-use the rule-based recommendations as bullets
    how_text = "How Bivenue helped:\n" + rule_based_summary
    y2 = _draw_paragraph(draw, how_text, col2_x, y2, col_width, body_font)

    # --- Column 3: Outcome (AI brief) ---
    y3 = top
    draw.text((col3_x, y3), "Outcome", font=section_title_font, fill=brand_blue)
    y3 += 32
    draw.line([(col3_x, y3), (col3_x + col_width, y3)], fill=accent_blue, width=4)
    y3 += 16

    outcome_intro = "Outcome & AI deep-dive insights:"
    y3 = _draw_paragraph(draw, outcome_intro, col3_x, y3, col_width, body_font)

    # We don’t want to repeat the title if the AI brief starts with "# Intercompany…"
    cleaned_ai_brief = ai_brief.strip()
    if cleaned_ai_brief.startswith("#"):
        # Drop the first line (the Markdown heading)
        cleaned_ai_brief = "\n".join(cleaned_ai_brief.splitlines()[1:]).strip()

    y3 = _draw_paragraph(draw, cleaned_ai_brief, col3_x, y3, col_width, small_font)

    # --- Footer note ---
    footer_text = "This brief was generated by Bivenue Copilot – AI-assisted Finance Transformation Advisor."
    fw, fh = draw.textsize(footer_text, font=small_font)
    draw.text(
        ((width - fw) // 2, height - fh - 20),
        footer_text,
        font=small_font,
        fill=brand_blue,
    )

    # --- Export to PDF ---
    buffer = BytesIO()
    image.save(buffer, format="PDF")
    buffer.seek(0)
    return buffer.getvalue()
