# engine/pdf_export.py

from __future__ import annotations

from io import BytesIO
from typing import Optional, List, Tuple

from PIL import Image, ImageDraw, ImageFont

# Basic page geometry (A4-ish at 150 dpi)
PAGE_WIDTH = 1654
PAGE_HEIGHT = 2339

BANNER_HEIGHT = 260
MARGIN = 80
COLUMN_GAP = 40


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Try to load a decent TTF font; fall back to default if not available.
    """
    for name in ["DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_text(
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    draw: ImageDraw.ImageDraw,
) -> List[str]:
    """
    Simple word-wrap helper.
    """
    words = text.split()
    if not words:
        return []

    lines: List[str] = []
    current: List[str] = []

    for w in words:
        test_line = " ".join(current + [w])
        w_width, _ = draw.textsize(test_line, font=font)
        if w_width <= max_width:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]

    if current:
        lines.append(" ".join(current))
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
    Draw a wrapped paragraph and return the new y position after the block.
    """
    lines = _wrap_text(text, font, width, draw)
    line_height = font.getsize("Ag")[1]

    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height + line_spacing

    return y


def _draw_top_banner(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    logo_path: Optional[str],
    company_name: str,
    industry: Optional[str],
) -> None:
    """
    Top dark-blue banner with *only logo on the left* and Company Profile card on the right.
    No 'Bivenue Copilot' text.
    """
    banner_color = "#003966"
    draw.rectangle([(0, 0), (PAGE_WIDTH, BANNER_HEIGHT)], fill=banner_color)

    # --- Left: Logo only ---
    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # Fit logo into a fixed box
            target_h = 120
            ratio = target_h / logo.height
            target_w = int(logo.width * ratio)
            logo = logo.resize((target_w, target_h), Image.LANCZOS)

            logo_x = MARGIN
            logo_y = BANNER_HEIGHT // 2 - target_h // 2
            img.paste(logo, (logo_x, logo_y), logo)
        except Exception:
            # Silent fail if logo can't be loaded
            pass

    # --- Right: Company profile card ---
    card_width = 520
    card_height = 200
    card_x = PAGE_WIDTH - MARGIN - card_width
    card_y = BANNER_HEIGHT // 2 - card_height // 2

    draw.rounded_rectangle(
        [(card_x, card_y), (card_x + card_width, card_y + card_height)],
        radius=25,
        fill="white",
    )

    title_font = _load_font(32)
    body_font = _load_font(24)

    draw.text(
        (card_x + 24, card_y + 18),
        "Company Profile",
        font=title_font,
        fill=banner_color,
    )

    y = card_y + 70
    draw.text(
        (card_x + 24, y),
        f"Name: {company_name}",
        font=body_font,
        fill="black",
    )
    y += 36
    if industry:
        draw.text(
            (card_x + 24, y),
            f"Industry: {industry}",
            font=body_font,
            fill="black",
        )


def _draw_consulting_columns(
    draw: ImageDraw.ImageDraw,
    challenge: str,
    domain: str,
    rule_based_summary: str,
    ai_brief: str,
) -> int:
    """
    Three-column layout:
      1) Mission-critical priority
      2) How Bivenue helped
      3) Outcome & AI deep-dive insights
    Returns the y position after this block, so we can draw benefits below.
    """
    heading_font = _load_font(30)
    body_font = _load_font(24)

    top_y = BANNER_HEIGHT + 80
    usable_width = PAGE_WIDTH - 2 * MARGIN
    col_width = (usable_width - 2 * COLUMN_GAP) // 3

    # Column X positions
    col1_x = MARGIN
    col2_x = col1_x + col_width + COLUMN_GAP
    col3_x = col2_x + col_width + COLUMN_GAP

    # --- Column 1: Mission-critical priority ---
    draw.text(
        (col1_x, top_y),
        "Mission-critical priority",
        font=heading_font,
        fill="#003966",
    )
    y1 = top_y + 50
    mission_text = f"Mission-critical priority: {domain or 'Finance'}"
    y1 = _draw_paragraph(draw, mission_text, col1_x, y1, col_width, body_font)

    # --- Column 2: How Bivenue helped ---
    draw.text(
        (col2_x, top_y),
        "How Bivenue helped",
        font=heading_font,
        fill="#003966",
    )
    y2 = top_y + 50
    how_text = rule_based_summary or "Summary of recommended focus areas & actions."
    y2 = _draw_paragraph(draw, how_text, col2_x, y2, col_width, body_font)

    # --- Column 3: Outcome & AI deep-dive ---
    draw.text(
        (col3_x, top_y),
        "Outcome & AI deep-dive insights",
        font=heading_font,
        fill="#003966",
    )
    y3 = top_y + 50
    outcome_text = ai_brief or "AI analysis could not be generated."
    y3 = _draw_paragraph(draw, outcome_text, col3_x, y3, col_width, body_font)

    return max(y1, y2, y3)


def _draw_benefits_strip(
    draw: ImageDraw.ImageDraw,
    top_y: int,
) -> None:
    """
    Draw a BCG-style horizontal benefits strip:
    5 rounded boxes with green accents and short text.
    """
    heading_font = _load_font(26)
    body_font = _load_font(22)

    # You can tweak these to your liking
    benefits: List[Tuple[str, str]] = [
        (
            "Leading by example",
            "Finance sets the tone for change by role-modelling new ways of working.",
        ),
        (
            "Improved decisions",
            "Cleaner data, standard reports and analytics support faster decisions.",
        ),
        (
            "Smarter resources",
            "Capacity is redirected from manual work to higher-value analysis.",
        ),
        (
            "More meaningful work",
            "Teams focus on business impact rather than repetitive reconciliations.",
        ),
        (
            "Future-ready finance",
            "Digital tools and AI build skills needed for the next wave of change.",
        ),
    ]

    strip_left = MARGIN
    strip_right = PAGE_WIDTH - MARGIN
    total_width = strip_right - strip_left
    box_gap = 20
    box_width = (total_width - box_gap * (len(benefits) - 1)) // len(benefits)
    box_height = 210

    green = "#00a96d"

    for i, (title, text) in enumerate(benefits):
        x = strip_left + i * (box_width + box_gap)
        y = top_y

        # Box
        draw.rounded_rectangle(
            [(x, y), (x + box_width, y + box_height)],
            radius=35,
            outline=green,
            width=3,
            fill="white",
        )

        # Title (green)
        draw.text(
            (x + 18, y + 18),
            title,
            font=heading_font,
            fill=green,
        )

        # Body text
        body_y = y + 18 + 40
        _draw_paragraph(
            draw,
            text,
            x + 18,
            body_y,
            box_width - 36,
            body_font,
            fill="black",
        )


def create_consulting_brief_pdf(
    logo_path: Optional[str],
    domain: str,
    challenge: str,
    rule_based_summary: str,
    ai_brief: str,
    company_name: str = "Client",
    industry: Optional[str] = "Finance",
    revenue: Optional[str] = None,      # kept for future use
    employees: Optional[str] = None,    # kept for future use
) -> bytes:
    """
    Create a one-page PDF consulting brief with:
      - Top banner (logo + company profile)
      - 3 consulting columns
      - BCG-style benefits strip at the bottom
    """
    # --- Base image ---
    img = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
    draw = ImageDraw.Draw(img)

    # --- Header banner (logo only + company profile) ---
    _draw_top_banner(img, draw, logo_path, company_name, industry)

    # --- Consulting content columns ---
    bottom_y = _draw_consulting_columns(
        draw=draw,
        challenge=challenge,
        domain=domain,
        rule_based_summary=rule_based_summary,
        ai_brief=ai_brief,
    )

    # --- Benefits strip (BCG-style flow) ---
    benefits_top = bottom_y + 80
    if benefits_top + 220 < PAGE_HEIGHT - 80:
        _draw_benefits_strip(draw, benefits_top)

    # --- Export to PDF (via RGB image) ---
    output = BytesIO()
    img.save(output, format="PDF")
    return output.getvalue()
