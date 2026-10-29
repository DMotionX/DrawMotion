"""
Automated unit tests for Phase 2: Dedicated WritingHandItem & Animator Engine Decoupling.
Verifies complete isolation of WritingHandItem, zero-drift tip alignment, and dynamic hand switching
between whiteboard drawing and text handwriting in AnimatorEngine.
"""

import os
import pytest
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainterPath, QColor

app = QApplication.instance()
if app is None:
    app = QApplication([])

from components.write_to_image.hand_manager import WritingHandItem, TextHandManager
from components.write_to_image.hand_catalog import WritingHandCatalog, NATIVE_WIDTH
from graphics.hand_item import HandItem
from core.animator_engine import AnimatorEngine
from core.settings_manager import SettingsManager
from graphics.animated_stroke_item import AnimatedStrokeItem
from components.write_to_image.models import WriteToImageModel
from components.write_to_image.graphics_item import WriteToImageGraphicsItem


def test_writing_hand_item_initialization():
    """Verify WritingHandItem initializes with default model, ZValue 9999, and calibrated tip offset."""
    sm = SettingsManager()
    sm.set("writing_hand_type", "right")
    sm.set("writing_hand_style", "style_01")

    scene = QGraphicsScene()
    wh = WritingHandItem(scene=scene)
    
    assert wh.zValue() == 9999
    assert not wh.isVisible()
    assert wh.scene() is scene
    assert wh.current_hand_type == "right"
    assert wh.current_style_id == "style_01"

    assert not wh.pixmap().isNull()
    assert wh.pixmap().width() == WritingHandItem.BASE_RENDER_WIDTH

    # Tip offset verification: tip at item local (0, 0)
    scale_factor = WritingHandItem.BASE_RENDER_WIDTH / float(NATIVE_WIDTH)
    expected_offset = WritingHandCatalog.get_tip_offset("right", "style_01", scale=scale_factor)
    assert wh.offset().x() == pytest.approx(expected_offset.x(), abs=0.1)
    assert wh.offset().y() == pytest.approx(expected_offset.y(), abs=0.1)


def test_writing_hand_model_switch():
    """Verify switching hand types and models updates pixmap and tip offset accordingly."""
    wh = WritingHandItem()
    
    # Switch to left hand style 02
    wh.set_hand("left", "style_02")
    assert wh.current_hand_type == "left"
    assert wh.current_style_id == "style_02"
    assert not wh.pixmap().isNull()
    
    scale_factor = WritingHandItem.BASE_RENDER_WIDTH / float(NATIVE_WIDTH)
    expected_offset_l2 = WritingHandCatalog.get_tip_offset("left", "style_02", scale=scale_factor)
    assert wh.offset().x() == pytest.approx(expected_offset_l2.x(), abs=0.1)
    assert wh.offset().y() == pytest.approx(expected_offset_l2.y(), abs=0.1)

    # Switch to 'none'
    wh.set_hand("right", "none")
    assert wh.pixmap().isNull()
    assert not wh.isVisible()


def test_writing_hand_zero_drift_positioning():
    """Verify mapToScene(0, 0) perfectly hits target scene coordinate across multiple scales."""
    wh = WritingHandItem()
    wh.set_hand("right", "style_01")
    
    target_points = [
        QPointF(0.0, 0.0),
        QPointF(150.0, 250.0),
        QPointF(-320.5, 412.3),
    ]
    scales = [0.5, 1.0, 2.5, 3.0]
    
    for target in target_points:
        for s in scales:
            wh.setScale(s)
            wh.update_position(target, is_writing=True)
            tip_in_scene = wh.mapToScene(QPointF(0, 0))
            assert tip_in_scene.x() == pytest.approx(target.x(), abs=1e-3)
            assert tip_in_scene.y() == pytest.approx(target.y(), abs=1e-3)


def test_text_hand_manager_wrapper_compatibility():
    """Verify legacy TextHandManager wrapper provides full backward compatibility."""
    scene = QGraphicsScene()
    thm = TextHandManager(scene=scene)
    
    assert thm.hand_item is not None
    assert thm.hand_item.scene() is scene
    
    target = QPointF(50.0, 75.0)
    thm.update_position(target, is_drawing=True)
    assert thm.is_active is True
    assert thm.hand_item.isVisible()
    
    thm.update_position(target, is_drawing=False)
    assert thm.is_active is False
    assert not thm.hand_item.isVisible()
    
    thm.remove()
    assert thm.hand_item not in scene.items()


def test_animator_engine_hand_decoupling():
    """
    CRITICAL ARCHITECTURAL TEST:
    Verify AnimatorEngine shows hand_item for strokes and writing_hand_item for text items,
    guaranteeing zero cross-interference and complete separation of concerns.
    """
    scene = QGraphicsScene()
    draw_hand = HandItem()
    write_hand = WritingHandItem(scene=scene)
    scene.addItem(draw_hand)
    
    draw_hand.hide()
    write_hand.hide()
    
    engine = AnimatorEngine(draw_hand, parent=None, writing_hand_item=write_hand)
    
    # Create whiteboard stroke item
    path = QPainterPath()
    path.moveTo(0, 0)
    path.lineTo(100, 100)
    stroke_item = AnimatedStrokeItem(path)
    stroke_item.anim_duration = 1.0
    scene.addItem(stroke_item)
    
    # Create text item
    model = WriteToImageModel(id="test_txt", name="Decouple Text", text="Decoupled Text")
    model.duration = 1.0
    text_item = WriteToImageGraphicsItem(model)
    scene.addItem(text_item)
    
    # 1. Play queue with both stroke and text
    engine.sync_queue([stroke_item, text_item])
    assert len(engine.schedule) >= 2
    
    # Action 0 is stroke: draw_hand must be active, write_hand must be hidden
    engine.seek(0.5, show_hand_when_stopped=True)
    assert engine.hand_item.isVisible()
    assert not engine.writing_hand_item.isVisible()
    
    # Action 1 is text: draw_hand must be hidden, write_hand must be active
    # Find text action start time
    text_action = None
    for a in engine.schedule:
        if a.get('item') is text_item and a.get('type') == 'draw':
            text_action = a
            break
    assert text_action is not None
    mid_text_time = text_action['start'] + 0.2
    
    engine.seek(mid_text_time, show_hand_when_stopped=True)
    assert not engine.hand_item.isVisible()
    assert engine.writing_hand_item.isVisible()
    
    # 2. Stop engine: both hands must be cleanly hidden
    engine.stop()
    assert not engine.hand_item.isVisible()
    assert not engine.writing_hand_item.isVisible()
