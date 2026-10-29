"""
Unit tests for the decoupled Text Effects package and its QML-ready architecture.
"""

import pytest
from PySide6.QtGui import QImage, QPainter, QColor, QFont
from PySide6.QtCore import Qt

from components.write_to_image.effects import (
    apply_text_effect,
    AVAILABLE_EFFECTS,
    TextEffectsBridge,
    TextEffectsWidget,
)


@pytest.fixture(autouse=True)
def ensure_qapp(qapp):
    return qapp


def test_available_effects_catalog():
    """Verify all defined effects exist in AVAILABLE_EFFECTS catalog."""
    assert len(AVAILABLE_EFFECTS) >= 7
    ids = [eff["id"] for eff in AVAILABLE_EFFECTS]
    expected_ids = ["none", "glow", "neon", "ink_bleed", "drop_shadow", "glitch", "holographic"]
    for eid in expected_ids:
        assert eid in ids, f"Expected {eid} in AVAILABLE_EFFECTS"


def test_apply_each_effect_to_image():
    """Verify each effect processes a QImage and returns a valid non-empty ARGB32 image."""
    width, height = 200, 80
    base_img = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
    base_img.fill(Qt.transparent)
    p = QPainter(base_img)
    p.setFont(QFont("Arial", 28))
    p.setPen(QColor(255, 255, 255))
    p.drawText(base_img.rect(), Qt.AlignCenter, "Effect Test")
    p.end()

    for eff in AVAILABLE_EFFECTS:
        eff_id = eff["id"]
        res = apply_text_effect(base_img, eff_id, "#ff5500")
        assert isinstance(res, QImage)
        assert res.width() == width
        assert res.height() == height
        assert not res.isNull()


def test_text_effects_bridge():
    """Verify TextEffectsBridge signals and slots for QML integration."""
    bridge = TextEffectsBridge()
    assert bridge.currentEffect == "none"

    emitted_effects = []
    bridge.effectChanged.connect(lambda e: emitted_effects.append(e))

    bridge.setEffect("neon")
    assert bridge.currentEffect == "neon"
    assert emitted_effects == ["neon"]

    emitted_colors = []
    bridge.colorChanged.connect(lambda c: emitted_colors.append(c))
    bridge.setColor("#00ffcc")
    assert bridge.currentColor == "#00ffcc"
    assert emitted_colors == ["#00ffcc"]

    emitted_intensities = []
    bridge.intensityChanged.connect(lambda i: emitted_intensities.append(i))
    bridge.setIntensity(1.5)
    assert abs(bridge.currentIntensity - 1.5) < 1e-4
    assert len(emitted_intensities) == 1


def test_text_effects_widget_initialization():
    """Verify TextEffectsWidget initializes safely with fallback or QML."""
    widget = TextEffectsWidget()
    assert widget is not None
    assert widget.current_effect() == "none"

    changed = []
    widget.effect_changed.connect(lambda e: changed.append(e))
    widget.set_effect("glow")
    assert widget.current_effect() == "glow"
    assert "glow" in changed
