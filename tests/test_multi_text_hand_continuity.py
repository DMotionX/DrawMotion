import pytest
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtGui import QPainterPath
from PySide6.QtCore import QPointF

from core.animator_engine import AnimatorEngine
from components.write_to_image.models import WriteToImageModel
from components.write_to_image.graphics_item import WriteToImageGraphicsItem
from graphics.hand_item import HandItem
from components.write_to_image.hand_manager import WritingHandItem
from graphics.animated_stroke_item import AnimatedStrokeItem
from core.settings_manager import SettingsManager


@pytest.fixture(autouse=True)
def clean_settings(qapp):
    sm = SettingsManager()
    orig_hand_style = sm.get("hand_style", "default")
    orig_wh_style = sm.get("writing_hand_style", "default")
    sm.set("hand_style", "default")
    sm.set("writing_hand_style", "default")
    yield qapp
    sm.set("hand_style", orig_hand_style)
    sm.set("writing_hand_style", orig_wh_style)


def test_multi_text_hand_continuity_and_leak_prevention(qapp):
    """
    Verifies that when animating sequential text items:
    1. Whiteboard drawing hand (HandItem) NEVER leaks or appears (isVisible() == False throughout).
    2. The hand is strictly hidden between text frames during transit.
    3. WritingHandItem writes Item 1, hides in the gap, and appears cleanly for Item 2.
    """
    scene = QGraphicsScene()
    board_hand = HandItem()
    writing_hand = WritingHandItem(scene=scene)
    scene.addItem(board_hand)

    engine = AnimatorEngine(board_hand, writing_hand_item=writing_hand)

    model1 = WriteToImageModel(id="txt1", name="Text 1", text="السلام عليكم ورحمة الله وبركاته", duration=3.0)
    item1 = WriteToImageGraphicsItem(model1)
    item1.anim_delay = 0.0
    item1.anim_duration = 3.0
    item1.setPos(100, 100)

    model2 = WriteToImageModel(id="txt2", name="Text 2", text="النهاردة هنتكلم في موضوع مهم", duration=3.0)
    item2 = WriteToImageGraphicsItem(model2)
    item2.anim_delay = 3.0
    item2.anim_duration = 3.0
    item2.setPos(100, 300)

    scene.addItem(item1)
    scene.addItem(item2)

    engine.sync_queue([item1, item2])
    assert len(engine.schedule) >= 3, "Schedule should contain Item 1, move-hand transit, and Item 2"

    move_action = engine.schedule[1]
    assert move_action['type'] == 'move-hand'
    assert move_action.get('is_text_transition') is True, "move-hand between two text items must be flagged as text transition"

    engine.play()

    # Step through entire timeline in 16ms increments
    t = 0.0
    while t <= 7.0:
        engine._step_internal(16)
        t += 0.016
        engine.total_time_passed = t

        # CRITICAL ASSERTION: The drawing hand (HandItem) must NEVER leak into text animations!
        assert not board_hand.isVisible(), f"LEAK DETECTED at t={t:.3f}s: HandItem was visible during text scene!"

        # During transit between text items, the hand must be strictly HIDDEN
        if move_action['start'] < t < move_action['end']:
            assert not writing_hand.isVisible(), f"Hand should be hidden between frames during transit at t={t:.3f}s"


def test_pure_drawing_strokes_hand_item_intact(qapp):
    """
    Verifies that the Whiteboard Drawing Engine is 100% UNTOUCHED and fully functional:
    HandItem continues to draw and move between whiteboard stroke items as expected.
    """
    scene = QGraphicsScene()
    board_hand = HandItem()
    writing_hand = WritingHandItem(scene=scene)
    scene.addItem(board_hand)

    engine = AnimatorEngine(board_hand, writing_hand_item=writing_hand)

    p1 = QPainterPath()
    p1.moveTo(0, 0)
    p1.lineTo(100, 100)
    s1 = AnimatedStrokeItem(p1)
    s1.anim_duration = 2.0
    s1.duration = 2.0
    s1.setPos(50, 50)

    p2 = QPainterPath()
    p2.moveTo(0, 0)
    p2.lineTo(200, 200)
    s2 = AnimatedStrokeItem(p2)
    s2.anim_duration = 2.0
    s2.duration = 2.0
    s2.setPos(300, 300)

    scene.addItem(s1)
    scene.addItem(s2)

    engine.sync_queue([s1, s2])
    move_action = engine.schedule[1]
    assert move_action['type'] == 'move-hand'
    assert move_action.get('is_text_transition') is False, "Stroke-to-stroke move-hand must not be flagged as text transition"

    # During stroke 1 drawing (1.0s): board_hand is visible, writing_hand is hidden
    engine.seek(1.0, show_hand_when_stopped=True)
    assert board_hand.isVisible(), "Drawing engine HandItem must remain visible while drawing strokes"
    assert not writing_hand.isVisible()

    # During stroke transit (around 2.3s): board_hand is visible moving between strokes
    transit_mid = (move_action['start'] + move_action['end']) / 2.0
    engine.seek(transit_mid, show_hand_when_stopped=True)
    assert board_hand.isVisible(), "Drawing engine HandItem must remain visible during transit between whiteboard strokes"
    assert not writing_hand.isVisible()


def test_mixed_scene_transition_boundary(qapp):
    """
    Verifies clean hand-off between Text item and Stroke item:
    1. During text: WritingHandItem is active, HandItem is hidden.
    2. During stroke: HandItem is active, WritingHandItem is hidden.
    """
    scene = QGraphicsScene()
    board_hand = HandItem()
    writing_hand = WritingHandItem(scene=scene)
    scene.addItem(board_hand)

    engine = AnimatorEngine(board_hand, writing_hand_item=writing_hand)

    model = WriteToImageModel(id="txt_mix", name="Text Mix", text="Mixed Scene Text", duration=2.0)
    text_item = WriteToImageGraphicsItem(model)
    text_item.anim_duration = 2.0
    text_item.setPos(50, 50)

    p = QPainterPath()
    p.moveTo(0, 0)
    p.lineTo(150, 150)
    stroke = AnimatedStrokeItem(p)
    stroke.anim_duration = 2.0
    stroke.duration = 2.0
    stroke.setPos(200, 200)

    scene.addItem(text_item)
    scene.addItem(stroke)

    engine.sync_queue([text_item, stroke])

    # Time 1.0s (in text): writing_hand active, board_hand hidden
    engine.seek(1.0, show_hand_when_stopped=True)
    assert writing_hand.isVisible()
    assert not board_hand.isVisible()

    # Time 3.5s (in stroke): board_hand active, writing_hand hidden
    stroke_start = engine.schedule[2]['start']
    engine.seek(stroke_start + 0.5, show_hand_when_stopped=True)
    assert board_hand.isVisible()
    assert not writing_hand.isVisible()


def test_text_item_duplication_and_serialization(qapp):
    """
    Verifies that WriteToImageGraphicsItem preserves all writing hand model properties
    when serialized to/from dict (e.g. during duplicate or save/load).
    """
    model = WriteToImageModel(
        id="orig_id",
        name="Orig Text",
        text="Sample Arabic Text",
        writing_hand_type="right",
        writing_hand_style="style_03",
        writing_hand_size=1.4,
        text_align="right"
    )
    orig_item = WriteToImageGraphicsItem(model)
    d = orig_item.to_dict()

    restored = WriteToImageGraphicsItem.from_dict(d)
    assert restored.model.text == "Sample Arabic Text"
    assert restored.model.writing_hand_type == "right"
    assert restored.model.writing_hand_style == "style_03"
    assert restored.model.writing_hand_size == 1.4
    assert restored.model.text_align == "right"
    assert "WriteTo" in restored.__class__.__name__
