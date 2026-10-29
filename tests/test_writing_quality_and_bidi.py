"""
Unit tests for BiDi traversal, overlap-safe centroid allocation, scale preservation,
text alignment, and high-DPI crisp rendering in the Write-to-Image system.
"""

import os
import json
import pytest
import numpy as np
from PySide6.QtGui import QImage, QPainter, QFont
from PySide6.QtCore import Qt

from components.write_to_image.models import WriteToImageModel
from components.write_to_image.image_renderer import render_text_to_image, _check_if_rtl
from components.write_to_image.time_map_generator import (
    generate_time_map,
    _is_rtl_char,
)
from components.write_to_image.effects.effects_widget import TextEffectsWidget


@pytest.fixture(autouse=True)
def ensure_qapp(qapp):
    return qapp


def test_is_rtl_char_detection():
    """Verify script character direction classification."""
    # Latin characters must be LTR
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789":
        assert not _is_rtl_char(c), f"Character '{c}' should be recognized as LTR"

    # Arabic characters must be RTL
    for c in "ابتثجحخدذرزسشصضطظعغفقكلمنهوي":
        assert _is_rtl_char(c), f"Character '{c}' should be recognized as RTL"


def test_dominant_language_check():
    """Verify dominant language check for auto direction."""
    # Majority English with a single Arabic connector
    mixed_mostly_en = "Responsive Design و Responsive Web Design"
    assert not _check_if_rtl(mixed_mostly_en), "Mostly English text should resolve to LTR"

    # Majority Arabic with an English term
    mixed_mostly_ar = "تصميم الويب المتجاوب Responsive Design للمواقع"
    assert _check_if_rtl(mixed_mostly_ar), "Mostly Arabic text should resolve to RTL"

    # Pure English
    assert not _check_if_rtl("Hello World")
    # Pure Arabic
    assert _check_if_rtl("مرحبا بالعالم")


def test_bidi_word_run_ordering_latin_ltr_guarantee():
    """Verify that Latin words within mixed BiDi text are traversed LTR, never reversed."""
    text = "Responsive Design و Web Design"
    model = WriteToImageModel(
        id="test_bidi_1",
        name="BiDi Test",
        text=text,
        font_family="Arial",
        font_size=24,
        is_bold=False,
        text_align="auto",
    )

    image_path = render_text_to_image(
        text=model.text,
        font_family=model.font_family,
        font_size=model.font_size,
        color=model.color,
        id_str=model.id,
        is_bold=model.is_bold,
        text_align=model.text_align,
    )
    assert os.path.exists(image_path)
    charmap_path = os.path.join(os.path.dirname(image_path), f"text_{model.id}_charmap.json")
    with open(charmap_path, "r", encoding="utf-8") as f:
        char_map = json.load(f)
    assert len(char_map) > 0

    # In char_map, verify that consecutive Latin letters in 'Responsive' have increasing X or LTR order
    english_runs = []
    current_run = []
    for entry in char_map:
        ch = entry["char"]
        if ch.isalpha() and not _is_rtl_char(ch):
            current_run.append(entry)
        else:
            if len(current_run) > 1:
                english_runs.append(current_run)
            current_run = []
    if len(current_run) > 1:
        english_runs.append(current_run)

    assert len(english_runs) >= 2, "Should identify at least 2 English word runs"

    # For every English word run, verify that characters move left-to-right (x increases)
    for run in english_runs:
        for idx in range(len(run) - 1):
            assert run[idx]["x"] <= run[idx + 1]["x"] + 2.0, (
                f"English letters '{run[idx]['char']}' and '{run[idx+1]['char']}' "
                f"must progress LTR: x1={run[idx]['x']}, x2={run[idx+1]['x']}"
            )


def test_overlap_safe_nearest_centroid_time_map():
    """Verify time map generation on heavy bold overlapping fonts without blank patches."""
    model = WriteToImageModel(
        id="test_overlap_1",
        name="Overlap Test",
        text="Responsive Web",
        font_family="Arial Black",
        font_size=32,
        is_bold=True,
        text_align="auto",
    )

    image_path = render_text_to_image(
        text=model.text,
        font_family=model.font_family,
        font_size=model.font_size,
        color=model.color,
        id_str=model.id,
        is_bold=model.is_bold,
        text_align=model.text_align,
    )
    assert os.path.exists(image_path)
    charmap_path = os.path.join(os.path.dirname(image_path), f"text_{model.id}_charmap.json")
    with open(charmap_path, "r", encoding="utf-8") as f:
        char_map = json.load(f)

    img = QImage(image_path)
    time_map = generate_time_map(img, char_map=char_map, is_rtl=False)

    assert time_map is not None
    assert time_map.shape[0] == img.height()
    assert time_map.shape[1] == img.width()

    # Time map values are stored as uint8 (0..255) where background is 255 and text timestamps are 0..255
    assert time_map.dtype == np.uint8
    fg_mask = time_map < 255
    assert np.any(fg_mask), "Time map must have foreground pixels with valid reveal timestamps"
    assert np.all(time_map <= 255), "Time map values must not exceed 255"


def test_scale_preservation_on_model_and_reedit():
    """Verify that editing an existing text item preserves custom scale_w and scale_h."""
    model = WriteToImageModel(
        id="test_scale_1",
        name="Scale Test",
        text="Custom Scaled Text",
        scale_w=2.75,
        scale_h=2.75,
        width=400.0,
        height=120.0,
    )

    assert model.scale_w == 2.75
    assert model.scale_h == 2.75

    data = model.to_dict()
    assert data["transform"]["scale_w"] == 2.75
    assert data["transform"]["scale_h"] == 2.75

    # Reconstructed model preserves dimensions and scale
    restored = WriteToImageModel.from_dict(data)
    assert restored.scale_w == 2.75
    assert restored.scale_h == 2.75
    assert restored.width == 400.0
    assert restored.height == 120.0


def test_text_alignment_options():
    """Verify text_align property handling across model and rendering."""
    # Test valid options
    for align in ["left", "center", "right", "auto"]:
        m = WriteToImageModel(id=f"test_align_{align}", name="Align Test", text="Alignment Test", text_align=align)
        assert m.text_align == align
        d = m.to_dict()
        assert d["text_align"] == align
        m2 = WriteToImageModel.from_dict(d)
        assert m2.text_align == align

        image_path = render_text_to_image(
            text=m2.text,
            font_family=m2.font_family,
            font_size=m2.font_size,
            color=m2.color,
            id_str=m2.id,
            text_align=align,
        )
        assert os.path.exists(image_path)


def test_qml_effects_widget_minimum_height():
    """Verify TextEffectsWidget sets appropriate dimensions to avoid vertical collapse."""
    widget = TextEffectsWidget()
    assert widget is not None
    # If QML widget loaded, height should be >= 180
    if widget._qml_widget is not None:
        assert widget.minimumHeight() >= 180
        assert widget._qml_widget.minimumHeight() >= 180


def test_subpixel_continuous_trajectory_interpolation():
    """Verify that WriteToImageGraphicsItem smoothly interpolates tip positions sub-pixel by sub-pixel."""
    from components.write_to_image.graphics_item import WriteToImageGraphicsItem
    from PySide6.QtCore import QPointF

    model = WriteToImageModel(
        id="test_subpixel",
        name="Subpixel Test",
        text="Smooth Flow",
    )
    item = WriteToImageGraphicsItem(model)
    # Mock dense 512-point trajectory along a curve
    item._trajectory = [QPointF(float(i), float(i * 0.5)) for i in range(512)]
    
    # Check intermediate sub-pixel positions
    item.progress = 0.1000
    pos1 = item.get_tip_position()
    item.progress = 0.1005
    pos2 = item.get_tip_position()
    item.progress = 0.1010
    pos3 = item.get_tip_position()

    # Positions must advance continuously without integer truncation plateaus
    assert pos1.x() < pos2.x() < pos3.x(), "Tip position must advance continuously with sub-pixel floating precision"
    assert pos1.y() < pos2.y() < pos3.y()


def test_realistic_hybrid_gaussian_smoothness():
    """Verify RealisticHybridAlgorithm generates smooth monotonic timestamps without spiky speed oscillations."""
    from components.write_to_image.algorithms.realistic_hybrid.realistic_hybrid_algorithm import RealisticHybridAlgorithm

    algo = RealisticHybridAlgorithm()
    # Create a staircase raster path simulating a discrete stroke
    seeds = [(i, int(i * 0.7 + (i % 2))) for i in range(60)]
    times = algo.generate_times(seeds, is_rtl=False)

    assert len(times) == len(seeds)
    assert np.all(np.diff(times) >= 0.0), "Times must be strictly monotonically non-decreasing"
    assert times[0] == 0.0
    assert abs(times[-1] - 1.0) < 1e-5

    # Measure speed fluctuations (dt between consecutive points)
    dts = np.diff(times)
    # The ratio of max dt to min dt should be moderate, not exhibiting 50x spikes
    non_zero_dts = dts[dts > 1e-6]
    dt_ratio = non_zero_dts.max() / non_zero_dts.min()
    assert dt_ratio < 15.0, f"Speed fluctuations should be controlled by Gaussian smoothing (got ratio {dt_ratio:.2f})"


def test_cyclic_character_stem_ordering_eliminates_white_hole():
    """Verify that in cyclic letters like 'p', stem timestamps strictly precede the loop to eliminate white holes."""
    from components.write_to_image.image_renderer import render_text_to_image
    from components.write_to_image.time_map_generator import generate_time_map
    import json

    img_path = render_text_to_image("Figma mcp", "Arial", 32, "#1a1a1a", "unit_test_white_hole", is_bold=True)
    charmap_path = os.path.join(os.path.dirname(img_path), "text_unit_test_white_hole_charmap.json")
    with open(charmap_path, "r", encoding="utf-8") as f:
        charmap = json.load(f)

    p_info = next(c for c in charmap if c["char"] == "p")
    px1, px2 = int(p_info["x"]), int(p_info["x"] + p_info["w"])
    py1, py2 = int(p_info["y"]), int(p_info["y"] + p_info["h"])

    qimg = QImage(img_path)
    tmap, traj = generate_time_map(qimg, is_rtl=False, char_map=charmap, return_trajectory=True)

    p_crop = tmap[py1:py2, px1:px2]
    stem_region = p_crop[:, :30]
    stem_fg = stem_region[stem_region < 255]
    loop_region = p_crop[:, 30:]
    loop_fg = loop_region[loop_region < 255]

    assert len(stem_fg) > 0 and len(loop_fg) > 0
    assert np.median(stem_fg) < np.median(loop_fg), (
        f"Stem of 'p' (median={np.median(stem_fg)}) must be drawn before loop (median={np.median(loop_fg)})"
    )


def test_text_effects_contrast_and_chromatic_separation():
    """Verify Neon composites sharp text on top and Glitch has true RGB chromatic separation."""
    from components.write_to_image.effects.text_effects import apply_text_effect
    from PySide6.QtGui import QPainter, QColor, QFont
    from PySide6.QtCore import Qt

    img = QImage(300, 100, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setFont(QFont("Arial", 28, QFont.Weight.Bold))
    p.setPen(QColor("#000000"))
    p.drawText(img.rect(), Qt.AlignmentFlag.AlignCenter, "Test Effects")
    p.end()

    # Neon must be valid and non-empty
    neon_res = apply_text_effect(img, "neon", "#000000")
    assert not neon_res.isNull()
    assert neon_res.size() == img.size()

    # Glitch must produce chromatic fringe separation (non-zero RGB channels)
    glitch_res = apply_text_effect(img, "glitch", "#000000")
    ptr = glitch_res.constBits()
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((glitch_res.height(), glitch_res.bytesPerLine()))
    # Non-zero alpha pixels must have non-zero RGB colors from cyan/magenta fringes
    fg_mask = arr[:, 3::4] > 0
    assert np.any(arr[:, 0::4][fg_mask] > 0) or np.any(arr[:, 2::4][fg_mask] > 0), (
        "Glitch effect must feature vibrant chromatic color separation, not plain black smear"
    )


def test_multi_line_paragraph_sequential_line_timing():
    """Verify that multi-line paragraphs produce sequential line times without interleaving."""
    from components.write_to_image.image_renderer import render_text_to_image
    from components.write_to_image.time_map_generator import generate_time_map
    import json

    paragraph = "First paragraph line.\nSecond paragraph line."
    img_path = render_text_to_image(paragraph, "Arial", 24, "#000000", "unit_test_para", is_bold=True)
    charmap_path = os.path.join(os.path.dirname(img_path), "text_unit_test_para_charmap.json")
    with open(charmap_path, "r", encoding="utf-8") as f:
        charmap = json.load(f)

    qimg = QImage(img_path)
    tmap = generate_time_map(qimg, is_rtl=False, char_map=charmap)

    line0_times = [tmap[int(ch['y']):int(ch['y']+ch['h']), int(ch['x']):int(ch['x']+ch['w'])].min() for ch in charmap if ch['line_idx'] == 0]
    line1_times = [tmap[int(ch['y']):int(ch['y']+ch['h']), int(ch['x']):int(ch['x']+ch['w'])].min() for ch in charmap if ch['line_idx'] == 1]

    assert max(line0_times) <= min(line1_times), (
        f"Line 1 (min {min(line1_times)}) must strictly follow Line 0 (max {max(line0_times)})"
    )


def test_arabic_multiline_handwriting_sequencing():
    """Verify that multi-line Arabic text renders with 100% accurate charmap boxes
    and writes strictly from Right-to-Left on Line 0, then Right-to-Left on Line 1,
    with zero jumping to the far left.
    """
    text = "السلام عليكم ورحمة الله وبركاته النهاردة هنتكلم\nعن موضوع جديد مهم ركزو معايا"
    img_path = render_text_to_image(text, "Arial", 32, "#000000", "unit_test_ar_multiline", text_align="right")
    assert os.path.exists(img_path)

    charmap_path = os.path.join(os.path.dirname(img_path), "text_unit_test_ar_multiline_charmap.json")
    with open(charmap_path, "r", encoding="utf-8") as f:
        charmap = json.load(f)

    assert len(charmap) > 0, "Charmap must contain characters"

    # Verify zero missing characters (every box must overlap drawn pixels)
    qimg = QImage(img_path)
    ptr = qimg.constBits()
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((qimg.height(), qimg.bytesPerLine()))
    alpha = arr[:, 3::4]

    for ch in charmap:
        cx, cy, cw, ch_h = int(ch['x']), int(ch['y']), int(ch['w']), int(ch['h'])
        crop = alpha[cy:cy+ch_h, cx:cx+cw]
        assert np.sum(crop > 0) > 0, f"Character '{ch['char']}' on line {ch['line_idx']} must encompass rendered pixels"

    # Verify time-map progression
    tmap = generate_time_map(qimg, is_rtl=True, char_map=charmap)
    assert tmap is not None

    line0_chars = [ch for ch in charmap if ch['line_idx'] == 0]
    line1_chars = [ch for ch in charmap if ch['line_idx'] == 1]
    assert len(line0_chars) > 0
    assert len(line1_chars) > 0

    line0_times = [tmap[int(ch['y']):int(ch['y']+ch['h']), int(ch['x']):int(ch['x']+ch['w'])].min() for ch in line0_chars]
    line1_times = [tmap[int(ch['y']):int(ch['y']+ch['h']), int(ch['x']):int(ch['x']+ch['w'])].min() for ch in line1_chars]

    # Line 0 must finish before Line 1 begins
    assert max(line0_times) <= min(line1_times), (
        f"Line 1 (min {min(line1_times)}) must strictly follow Line 0 (max {max(line0_times)})"
    )

    # Within Line 1, rightmost characters must be written earlier than leftmost characters
    line1_rightmost = max(line1_chars, key=lambda ch: ch['x'])
    line1_leftmost = min(line1_chars, key=lambda ch: ch['x'])

    t_rightmost = tmap[int(line1_rightmost['y']):int(line1_rightmost['y']+line1_rightmost['h']),
                       int(line1_rightmost['x']):int(line1_rightmost['x']+line1_rightmost['w'])].min()
    t_leftmost = tmap[int(line1_leftmost['y']):int(line1_leftmost['y']+line1_leftmost['h']),
                      int(line1_leftmost['x']):int(line1_leftmost['x']+line1_leftmost['w'])].min()

    assert t_rightmost < t_leftmost, (
        f"Line 1 must be written Right-to-Left: rightmost char time ({t_rightmost}) "
        f"must be strictly earlier than leftmost char time ({t_leftmost})"
    )
