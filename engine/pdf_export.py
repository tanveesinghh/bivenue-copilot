# engine/pdf_export.py

from __future__ import annotations

from io import BytesIO
from typing import Tuple, Optional

from PIL import Image, ImageDraw, ImageFont


# ---------- Helpers ---------- #

def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Try to load a decent sans font. Fall back to default if none found.
    """
    candidates = ["DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> Tuple[list[str], int]:
    """
    Wrap text into a list of lines that fit into max_width.
    Returns (lines, total_height).
    """
    draw = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines: list[str] = []
    total_height = 0

    # split paragraphs
    for paragraph in text.split("\n"):
        paragraph = paragraph.rstrip()
        if not paragraph:
            # empty line -> paragraph break
            lines.append("")
            total_height += font.getbbox("Ag")[3]
            continue

        words = paragraph.split(" ")
        current_line = ""
        for word in words:
            test_line = word if not current_line else current_line + " " + word
            w, h = draw.textsize(test_line, font=font)
            if w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    total_height += h
                current_line = word
        if current_line:
            w, h = draw.textsize(current_line, font=font)
            lines.append(current_line)
            total_height += h

    return lines, total_height


def _draw_paragraph(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    x: int,
    y: int,
    max_width: int,
    fill: str = "black",
) -> int:
    """
    Draw wrapped text and return the new y position (after the block).
    """
    lines, _ = _wrap_text(text, font, max_width)
    line_height = font.getbbox("Ag")[3] + 4
    for line in lines:
        if line == "":
            y += line_height  # paragraph break
            continue
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def _clean_markdown(text: str) -> str:
    """
    Very simple markdown cleaner:
    - strips heading #'s
    - converts '* ' / '- ' into bullet '• '
    - strips surrounding **bold** markers
    """
    cleaned_lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()

        if not line:
            cleaned_lines.append("")
            continue

        # remove heading hashes
        while line.startswith("#"):
            line = line.lstrip("#").strip()

        # bullets
        if line.startswith("* "):
            line = "• " + line[2:]
        elif line.startswith("- "):
            line = "• " + line[2:]

        # very simple bold cleanup
        if line.startswith("**") and line.endswith("**") and len(line) > 4:
            line = line[2:-2].strip()

        # internal **bold** → just text
        line = line.replace("**", "")

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# ---------- Main Export Function ---------- #

def create_consulting_brief_pdf(
    logo_path: Optional[str],
    domain: str,
    challenge: str,
    rule_based_summary: str,
    ai_brief: str,
    company_name: str = "Client",
    industry: str = "Finance",
    revenue: Optional[str] = None,
    employees: Optional[str] = None,
) -> bytes:
    """
    Create a 1-page consulting brief styled roughly like the Gartner example.
    Returns PDF bytes.
    """

    # Page setup (A4-ish, landscape)
    width, height = 2480, 1754  # 300 DPI landscape A4-ish
    bg_color = "white"
    primary_blue = "#003b70"
    accent_blue = "#00a6ff"

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts
    title_font = _load_font(70)
    h1_font = _load_font(46)
    h2_font = _load_font(40)
    body_font = _load_font(30)
    small_font = _load_font(24)

    # ---------- Top banner ---------- #
    banner_height = 260
    draw.rectangle([0, 0, width, banner_height], fill=primary_blue)

    # Left: Bivenue Copilot title
    draw.text(
        (120, 70),
        "Bivenue Copilot",
        font=title_font,
        fill="white",
    )
    draw.text(
        (120, 150),
        "Intercompany Consulting Brief",
        font=body_font,
        fill="white",
    )

    # Right: company profile box
    box_w, box_h = 700, 200
    box_x = width - box_w - 120
    box_y = 40
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=bg_color)

    draw.text((box_x + 40, box_y + 20), "Company Profile", font=h2_font, fill=primary_blue)

    profile_y = box_y + 90
    draw.text((box_x + 40, profile_y), f"Name: {company_name}", font=small_font, fill="black")
    profile_y += 40
    draw.text((box_x + 40, profile_y), f"Industry: {industry}", font=small_font, fill="black")
    profile_y += 40
    if revenue:
        draw.text((box_x + 40, profile_y), f"Revenue: {revenue}", font=small_font, fill="black")
        profile_y += 40
    if employees:
        draw.text((box_x + 40, profile_y), f"Employees: {employees}", font=small_font, fill="black")

    # Optional logo on left of title (inside banner)
    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # scale logo to fit nicely in banner
            max_logo_height = 120
            ratio = max_logo_height / logo.height
            logo = logo.resize((int(logo.width * ratio), int(logo.height * ratio)))
            img.paste(logo, (40, 80), logo)
        except Exception:
            # logo is optional; ignore if there is a problem
            pass

    # ---------- Body layout: 3 columns ---------- #
    margin_x = 120
    top_y = banner_height + 80
    col_gap = 60
    col_width = (width - 2 * margin_x - 2 * col_gap) // 3

    # Column 1: Mission-critical priority
    col1_x = margin_x
    y1 = top_y

    draw.text((col1_x, y1), "Mission-critical priority", font=h1_font, fill=primary_blue)
    y1 += 55
    draw.line(
        [(col1_x, y1), (col1_x + col_width, y1)],
        fill=accent_blue,
        width=6,
    )
    y1 += 30

    mission_text = f"Mission-critical priority: {domain}"
    y1 = _draw_paragraph(draw, mission_text, body_font, col1_x, y1, col_width, fill="black")

    # Column 2: How Bivenue helped (rule-based summary condensed)
    col2_x = col1_x + col_width + col_gap
    y2 = top_y

    draw.text((col2_x, y2), "How Bivenue helped", font=h1_font, fill=primary_blue)
    y2 += 55
    draw.line(
        [(col2_x, y2), (col2_x + col_width, y2)],
        fill=accent_blue,
        width=6,
    )
    y2 += 30

    # Clean the rule-based markdown a bit for nicer PDF
    cleaned_rule = _clean_markdown(rule_based_summary)
    y2 = _draw_paragraph(draw, cleaned_rule, body_font, col2_x, y2, col_width, fill="black")

    # Column 3: Outcome & AI deep-dive insights (AI brief)
    col3_x = col2_x + col_width + col_gap
    y3 = top_y

    draw.text((col3_x, y3), "Outcome & AI deep-dive insights", font=h1_font, fill=primary_blue)
    y3 += 55
    draw.line(
        [(col3_x, y3), (col3_x + col_width, y3)],
        fill=accent_blue,
        width=6,
    )
    y3 += 30

    cleaned_ai = _clean_markdown(ai_brief)
    y3 = _draw_paragraph(draw, cleaned_ai, body_font, col3_x, y3, col_width, fill="black")

    # ---------- Footer ---------- #
    footer_text = (
        "This brief was generated by Bivenue Copilot – AI-assisted Finance Transformation Advisor."
    )
    ft_w, ft_h = draw.textsize(footer_text, font=small_font)
    draw.text(
        ((width - ft_w) // 2, height - ft_h - 40),
        footer_text,
        font=small_font,
        fill=primary_blue,
    )

    # ---------- Export to PDF ---------- #
    buffer = BytesIO()
    img.save(buffer, format="PDF")
    buffer.seek(0)
    return buffer.getvalue()
