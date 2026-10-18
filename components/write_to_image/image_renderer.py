import os
import re
import json
from PySide6.QtGui import QPainter, QFont, QColor, QImage, QTextLayout, QTextLine, QTextOption
from PySide6.QtCore import Qt, QRect, QRectF, QPointF
from utils.paths import get_app_data_dir


def _check_if_rtl(text: str) -> bool:
    if not text:
        return False
    return bool(re.search(r'[\u0600-\u06FF]', text))


def render_text_to_image(text: str, font_family: str, font_size: int, color: str, id_str: str, 
                         is_bold: bool = False, is_italic: bool = False, is_underline: bool = False, text_effect: str = "none") -> str:
    """
    Renders text to a high-resolution PNG file (5x scale for sharpness).
    Also saves a _charmap.json alongside the PNG with per-character bounding boxes
    so the TextRevealAlgorithm can do proper letter-by-letter animation.

    Returns the file path to the saved PNG.
    """
    if not text.strip():
        return ""

    scale_factor = 5.0
    # Convert point size to pixels (approx 1.333 on standard 96 DPI Windows) and then scale up
    high_res_font_size = int(font_size * 1.3333 * scale_factor)
    print(f"[DEBUG] render_text_to_image called with font_size={font_size}, high_res={high_res_font_size}")
    font = QFont(font_family)
    if high_res_font_size > 0:
        font.setPixelSize(high_res_font_size)
    else:
        font.setPointSize(36)
        
    font.setBold(is_bold)
    font.setItalic(is_italic)
    font.setUnderline(is_underline)

    is_rtl = _check_if_rtl(text)
    alignment = Qt.AlignmentFlag.AlignRight if is_rtl else Qt.AlignmentFlag.AlignLeft
    text_flag = alignment | Qt.TextFlag.TextWordWrap

    # ── Measure text bounds ───────────────────────────────────────────────────
    dummy_img = QImage(1, 1, QImage.Format.Format_ARGB32)
    dummy_painter = QPainter(dummy_img)
    dummy_painter.setFont(font)
    metrics = dummy_painter.fontMetrics()
    rect = metrics.boundingRect(QRect(0, 0, 4000, 4000), text_flag, text)
    dummy_painter.end()

    margin = int(20 * scale_factor)
    width = rect.width() + margin * 2
    height = rect.height() + margin * 2

    # ── Draw the high-res PNG ─────────────────────────────────────────────────
    img = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)

    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.setFont(font)
    painter.setPen(QColor(color))

    draw_rect = QRect(margin, margin, rect.width(), rect.height())
    painter.drawText(draw_rect, text_flag, text)
    painter.end()
    
    # Save base PNG for animation mask calculation
    save_dir = os.path.join(get_app_data_dir(), "assets", "write_to_image")
    os.makedirs(save_dir, exist_ok=True)
    base_file_path = os.path.join(save_dir, f"text_{id_str}.png")
    img.save(base_file_path, "PNG")

    # Save display PNG with effects applied
    display_img = img.copy()
    if text_effect and text_effect != "none":
        try:
            from components.write_to_image.effects.text_effects import apply_text_effect
            display_img = apply_text_effect(display_img, text_effect, color)
        except ImportError:
            pass

    display_file_path = os.path.join(save_dir, f"text_{id_str}_display.png")
    display_img.save(display_file_path, "PNG")

    # Build and save char map (runs on main thread but is fast enough for typical text)
    try:
        char_map = _build_char_map(text, font, is_rtl, margin, rect.width())
    except Exception:
        char_map = []
    map_path = os.path.join(save_dir, f"text_{id_str}_charmap.json")
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(char_map, f, ensure_ascii=False)

    return base_file_path


def _build_char_map(text: str, font: QFont, is_rtl: bool, margin: int, max_width: int) -> list:
    """
    Uses QTextLayout to determine the pixel bounding box of each character.
    Returns a list of dicts: [{char, x, y, w, h}, ...]
    """
    layout = QTextLayout(text, font)

    option = QTextOption()
    option.setWrapMode(QTextOption.WrapMode.WordWrap)
    if is_rtl:
        option.setTextDirection(Qt.LayoutDirection.RightToLeft)
        option.setAlignment(Qt.AlignmentFlag.AlignRight)
    else:
        option.setTextDirection(Qt.LayoutDirection.LeftToRight)
        option.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.setTextOption(option)

    layout.beginLayout()
    y_cursor = float(margin)
    metrics = None

    lines = []
    while True:
        line = layout.createLine()
        if not line.isValid():
            break
        line.setLineWidth(float(max_width))
        line.setPosition(QPointF(float(margin), y_cursor))
        y_cursor += line.height()
        lines.append(line)

    layout.endLayout()

    char_map = []
    for line_idx, line in enumerate(lines):
        line_rect = line.rect()
        start = line.textStart()
        length = line.textLength()

        for i in range(length):
            char_idx = start + i
            if char_idx >= len(text):
                break
            char = text[char_idx]
            if char in (' ', '\n', '\r'):
                continue

            # Get glyph x position within the line
            # PySide6: cursorToX returns (x_float, ok_bool) - must unpack!
            x_in_line, _ = line.cursorToX(char_idx)
            x_in_line_end, _ = line.cursorToX(char_idx + 1)

            x = min(x_in_line, x_in_line_end)
            w = abs(x_in_line_end - x_in_line)
            y = line_rect.top()
            h = line_rect.height()

            if w > 0:
                char_map.append({
                    "char": char,
                    "x": float(x),
                    "y": float(y),
                    "w": float(w),
                    "h": float(h),
                    "line_idx": line_idx,
                })

    return char_map
