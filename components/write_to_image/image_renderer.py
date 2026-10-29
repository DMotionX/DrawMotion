import os
import re
import json
from PySide6.QtGui import QPainter, QFont, QColor, QImage, QTextLayout, QTextLine, QTextOption, QFontMetrics
from PySide6.QtCore import Qt, QRect, QRectF, QPointF
from utils.paths import get_app_data_dir


def _check_if_rtl(text: str) -> bool:
    if not text:
        return False
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    return arabic_chars > english_chars


def render_text_to_image(text: str, font_family: str, font_size: int, color: str, id_str: str, 
                         is_bold: bool = False, is_italic: bool = False, is_underline: bool = False, 
                         text_effect: str = "none", text_align: str = "auto") -> str:
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
    font.setStyleStrategy(QFont.StyleStrategy.PreferQuality | QFont.StyleStrategy.PreferAntialias)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)

    is_rtl = _check_if_rtl(text)
    
    # Resolve alignment
    if text_align == "left":
        alignment = Qt.AlignmentFlag.AlignLeft
    elif text_align == "center":
        alignment = Qt.AlignmentFlag.AlignHCenter
    elif text_align == "right":
        alignment = Qt.AlignmentFlag.AlignRight
    else:  # "auto"
        alignment = Qt.AlignmentFlag.AlignRight if is_rtl else Qt.AlignmentFlag.AlignLeft

    # ── Single Source of Truth: Unified Layout with QTextLayout ─────────────────
    option = QTextOption()
    option.setWrapMode(QTextOption.WrapMode.WordWrap)
    option.setAlignment(alignment)
    if is_rtl:
        option.setTextDirection(Qt.LayoutDirection.RightToLeft)
    else:
        option.setTextDirection(Qt.LayoutDirection.LeftToRight)

    paragraphs = text.split('\n')
    max_wrap_w = int(680 * scale_factor)
    margin = int(20 * scale_factor)

    # Pass 1: Compute maximum natural line width under word-wrap constraint across all paragraphs
    max_line_w = 0.0
    for p in paragraphs:
        if not p.strip():
            continue
        layout1 = QTextLayout(p, font)
        layout1.setTextOption(option)
        layout1.beginLayout()
        while True:
            line = layout1.createLine()
            if not line.isValid():
                break
            line.setLineWidth(float(max_wrap_w))
            max_line_w = max(max_line_w, line.naturalTextWidth())
        layout1.endLayout()

    content_w = max(max_line_w, 10.0)

    # Pass 2: Position lines within snug content_w bounding box
    all_layout_data = []
    y_cursor = float(margin)
    fm = QFontMetrics(font)

    for p in paragraphs:
        layout = QTextLayout(p, font)
        layout.setTextOption(option)
        layout.beginLayout()
        p_lines = []
        if not p.strip():
            y_cursor += fm.height()
        else:
            while True:
                line = layout.createLine()
                if not line.isValid():
                    break
                line.setLineWidth(content_w)
                line.setPosition(QPointF(float(margin), y_cursor))
                y_cursor += line.height()
                p_lines.append(line)
        layout.endLayout()
        all_layout_data.append((layout, p_lines, p))

    width = int(content_w + margin * 2)
    height = int(y_cursor + margin)

    # ── Draw the high-res PNG using the unified layout ─────────────────────────
    img = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)

    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.setFont(font)
    painter.setPen(QColor(color))

    for layout, _, _ in all_layout_data:
        layout.draw(painter, QPointF(0, 0))
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

    # Build and save char map from the exact same layout lines
    char_map = _extract_char_map_from_paragraphs(all_layout_data)
    map_path = os.path.join(save_dir, f"text_{id_str}_charmap.json")
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(char_map, f, ensure_ascii=False)

    return base_file_path


def _extract_char_map_from_paragraphs(all_layout_data: list) -> list:
    """
    Extracts the bounding box of each character from the unified layout lines across paragraphs.
    Returns a list of dicts: [{char, x, y, w, h, line_idx}, ...]
    """
    char_map = []
    global_line_idx = 0

    for layout, p_lines, p_text in all_layout_data:
        for line in p_lines:
            line_rect = line.rect()
            start = line.textStart()
            length = line.textLength()

            for i in range(length):
                char_idx = start + i
                if char_idx >= len(p_text):
                    break
                char = p_text[char_idx]
                if char in (' ', '\n', '\r', '\t'):
                    continue

                # In PySide6, line.cursorToX returns (x_float, ok_bool) or x_float depending on build
                ret1 = line.cursorToX(char_idx)
                x_in_line = ret1[0] if isinstance(ret1, (tuple, list)) else ret1

                ret2 = line.cursorToX(char_idx + 1)
                x_in_line_end = ret2[0] if isinstance(ret2, (tuple, list)) else ret2

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
                        "line_idx": global_line_idx,
                    })

            global_line_idx += 1

    return char_map


def _build_char_map(text: str, font: QFont, is_rtl: bool, margin: int, max_width: int,
                    alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft) -> list:
    """Backward-compatible helper using the unified QTextLayout approach."""
    option = QTextOption()
    option.setWrapMode(QTextOption.WrapMode.WordWrap)
    option.setAlignment(alignment)
    if is_rtl:
        option.setTextDirection(Qt.LayoutDirection.RightToLeft)
    else:
        option.setTextDirection(Qt.LayoutDirection.LeftToRight)

    paragraphs = text.split('\n')
    all_layout_data = []
    y_cursor = float(margin)
    fm = QFontMetrics(font)

    for p in paragraphs:
        layout = QTextLayout(p, font)
        layout.setTextOption(option)
        layout.beginLayout()
        p_lines = []
        if not p.strip():
            y_cursor += fm.height()
        else:
            while True:
                line = layout.createLine()
                if not line.isValid():
                    break
                line.setLineWidth(float(max_width))
                line.setPosition(QPointF(float(margin), y_cursor))
                y_cursor += line.height()
                p_lines.append(line)
        layout.endLayout()
        all_layout_data.append((layout, p_lines, p))

    return _extract_char_map_from_paragraphs(all_layout_data)
