"""
Comprehensive automated unit tests verifying 100% decoupling between
whiteboard drawing hand (HandItem) and text handwriting engine (WritingHandItem),
dynamic ergonomic scale limits, and new default hand assets calibration.
"""

import os
import pytest
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainterPath, QColor, QImage

from components.write_to_image.hand_catalog import WritingHandCatalog, WRITING_HAND_REGISTRY
from components.write_to_image.hand_manager import WritingHandItem
from components.write_to_image.models import WriteToImageModel
from components.write_to_image.graphics_item import WriteToImageGraphicsItem
from graphics.hand_item import HandItem
from core.settings_manager import SettingsManager
from core.animator_engine import AnimatorEngine
from graphics.animated_stroke_item import AnimatedStrokeItem
from components.inspector import InspectorPanel


@pytest.fixture(autouse=True)
def isolate_settings(qapp):
    """Ensure settings are clean and restored after each test."""
    sm = SettingsManager()
    orig_hand_size = sm.get("hand_size", 2.0)
    orig_hand_style = sm.get("hand_style", "default")
    orig_wh_type = sm.get("writing_hand_type", "right")
    orig_wh_style = sm.get("writing_hand_style", "default")
    orig_wh_size = sm.get("writing_hand_size", 1.0)

    sm.set("hand_size", 2.0)
    sm.set("hand_style", "default")
    sm.set("writing_hand_type", "right")
    sm.set("writing_hand_style", "default")
    sm.set("writing_hand_size", 1.0)

    yield qapp

    sm.set("hand_size", orig_hand_size)
    sm.set("hand_style", orig_hand_style)
    sm.set("writing_hand_type", orig_wh_type)
    sm.set("writing_hand_style", orig_wh_style)
    sm.set("writing_hand_size", orig_wh_size)


def test_new_default_assets_existence_and_calibration():
    """Verify hand_right_default.png and hand_left_default.png load and have near-zero margin tips."""
    # Right default
    right_pix = WritingHandCatalog.get_pixmap("right", "default")
    assert right_pix is not None
    assert not right_pix.isNull()
    assert right_pix.width() == 1536
    assert right_pix.height() == 2304

    right_entry = WritingHandCatalog.get_entry("right", "default")
    assert right_entry["tip_x"] == 10.0
    assert right_entry["tip_y"] == 15.0

    # Left default
    left_pix = WritingHandCatalog.get_pixmap("left", "default")
    assert left_pix is not None
    assert not left_pix.isNull()
    assert left_pix.width() == 1536
    assert left_pix.height() == 2304

    left_entry = WritingHandCatalog.get_entry("left", "default")
    assert left_entry["tip_x"] == 1519.0
    assert left_entry["tip_y"] == 12.0


def test_dynamic_ergonomic_scaling_and_bounding():
    """Verify WritingHandItem scales proportionally with text height within ergonomic scene boundaries [280px, 520px]."""
    wh = WritingHandItem()

    # Case 1: Standard text (24pt -> approx 32px height at 1.0 scale)
    model_std = WriteToImageModel(id="txt_std", name="Std", text="Standard Text", font_size=24)
    item_std = WriteToImageGraphicsItem(model_std)
    wh.update_item_scale(item_std)
    render_width_std = wh.get_rendered_scene_width()
    # Must be comfortable natural human hand size on 1080p canvas (~370px)
    assert 350.0 <= render_width_std <= 400.0

    # Case 2: Giant font headline (200pt -> line height ~266px)
    model_giant = WriteToImageModel(id="txt_giant", name="Giant", text="Giant Title", font_size=200)
    item_giant = WriteToImageGraphicsItem(model_giant)
    wh.update_item_scale(item_giant)
    render_width_giant = wh.get_rendered_scene_width()
    # Must be strictly clamped to maximum ergonomic ceiling 520px
    assert render_width_giant == pytest.approx(520.0, abs=1.0)


def test_english_arabic_hand_scale_parity():
    """
    CRITICAL PARITY TEST:
    Verify WritingHandItem maintains visual parity between English (long lines, scale ~1.0)
    and Arabic (compact titles, scale ~3.5), preventing the tiny doll-hand bug.
    """
    wh = WritingHandItem()

    # English sentence item at scale 1.0 (typical wide bounding box)
    model_en = WriteToImageModel(id="txt_en", name="EN", text="Welcome to this video tutorial", font_size=24)
    item_en = WriteToImageGraphicsItem(model_en)
    item_en.setScale(1.0)
    wh.update_item_scale(item_en)
    en_width = wh.get_rendered_scene_width()

    # Arabic title item at scale 3.5 (typical auto-fitted title)
    model_ar = WriteToImageModel(id="txt_ar", name="AR", text="مرحبا بكم", font_size=24)
    item_ar = WriteToImageGraphicsItem(model_ar)
    item_ar.setScale(3.5)
    wh.update_item_scale(item_ar)
    ar_width = wh.get_rendered_scene_width()

    # Both must be within natural human hand scale on 1080p canvas
    assert 350.0 <= en_width <= 420.0, f"English hand width {en_width}px is out of ergonomic range"
    assert 400.0 <= ar_width <= 520.0, f"Arabic hand width {ar_width}px is out of ergonomic range"

    # Parity ratio: English hand must never be less than 70% of Arabic hand (previously was <30%)
    parity_ratio = en_width / ar_width
    assert parity_ratio >= 0.70, f"Parity ratio {parity_ratio:.2f} is too low"

    # Dynamic scaling: dragging handles to enlarge English text smoothly enlarges the hand
    item_en.setScale(2.0)
    wh.update_item_scale(item_en)
    en_width_scaled = wh.get_rendered_scene_width()
    assert en_width_scaled > en_width
    assert en_width_scaled <= 520.0



def test_drawing_hand_size_mutation_does_not_affect_writing_hand():
    """Verify changing whiteboard hand_size has ZERO effect on WritingHandItem."""
    sm = SettingsManager()
    wh = WritingHandItem()

    model = WriteToImageModel(id="txt_item", name="Item", text="Test Item", font_size=36)
    item = WriteToImageGraphicsItem(model)
    wh.update_item_scale(item)
    orig_scale = wh.scale()

    # Mutate whiteboard drawing hand size to extreme value
    sm.set("hand_size", 25.0)

    # Writing hand scale must not change at all
    wh.update_item_scale(item)
    assert wh.scale() == orig_scale


def test_writing_hand_mutation_does_not_affect_whiteboard_drawing_hand():
    """Verify changing writing_hand_size or writing_hand_style has ZERO effect on whiteboard HandItem."""
    sm = SettingsManager()
    board_hand = HandItem()
    orig_board_scale = board_hand.scale()

    # Mutate writing hand settings
    sm.set("writing_hand_size", 2.0)
    sm.set("writing_hand_style", "style_04")

    # Board hand must remain completely identical
    assert board_hand.scale() == orig_board_scale
    assert board_hand.current_style == "default"
    assert board_hand.zValue() == 9999


def test_inspector_panel_handwriting_controls_visibility():
    """Verify handwriting pen controls appear in Inspector exclusively for text items."""
    panel = InspectorPanel()

    assert hasattr(panel, "handwriting_pen_container")
    assert hasattr(panel, "hw_hand_combo")
    assert hasattr(panel, "hw_style_combo")
    assert hasattr(panel, "hw_size_slider")

    # Select text item -> handwriting container should show and be enabled, library engine hidden
    text_model = WriteToImageModel(id="inspect_txt", name="Inspect", text="Hello Inspector")
    text_item = WriteToImageGraphicsItem(text_model)
    panel.on_item_selected(text_item)
    assert not panel.handwriting_pen_container.isHidden()
    assert panel.hw_hand_combo.isEnabled()
    assert panel.hw_style_combo.isEnabled()
    assert panel.hw_size_slider.isEnabled()
    assert panel.library_engine_container.isHidden()

    # Select non-text item (e.g. stroke item) -> handwriting container should hide and be disabled
    path = QPainterPath()
    path.moveTo(0, 0)
    path.lineTo(100, 100)
    stroke_item = AnimatedStrokeItem(path)
    panel.on_item_selected(stroke_item)
    assert panel.handwriting_pen_container.isHidden()
    assert not panel.hw_hand_combo.isEnabled()
    assert not panel.hw_style_combo.isEnabled()
    assert not panel.hw_size_slider.isEnabled()


def test_animator_engine_dual_scene_decoupling():
    """Verify AnimatorEngine seamlessly runs both drawing and writing hands with their isolated geometry."""
    scene = QGraphicsScene()
    board_hand = HandItem()
    scene.addItem(board_hand)
    writing_hand = WritingHandItem(scene=scene)
    engine = AnimatorEngine(board_hand, writing_hand_item=writing_hand)

    # Stroke item (draws with whiteboard hand)
    path = QPainterPath()
    path.moveTo(0, 0)
    path.lineTo(150, 150)
    stroke = AnimatedStrokeItem(path)
    stroke.anim_duration = 1.0
    stroke.duration = 1.0

    # Text item (writes with writing hand)
    text_model = WriteToImageModel(id="dual_txt", name="Dual", text="Dual Scene", writing_hand_style="default")
    text_item = WriteToImageGraphicsItem(text_model)
    text_item.anim_duration = 1.0
    text_item.duration = 1.0

    scene.addItem(stroke)
    scene.addItem(text_item)
    engine.sync_queue([stroke, text_item])

    # During stroke animation (time = 0.5s): board_hand active, writing_hand hidden
    engine.seek(0.5, show_hand_when_stopped=True)
    assert board_hand.isVisible()
    assert not writing_hand.isVisible()

    # During text animation (time = 1.5s): writing_hand active, board_hand hidden
    engine.seek(1.5, show_hand_when_stopped=True)
    assert not board_hand.isVisible()
    assert writing_hand.isVisible()
