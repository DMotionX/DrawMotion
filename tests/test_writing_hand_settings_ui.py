import pytest
from PySide6.QtWidgets import QApplication
from core.settings_manager import SettingsManager
from components.settings.components.drawing_settings import DrawingSettings
from components.write_to_image.hand_manager import WritingHandItem
from components.write_to_image.hand_catalog import WritingHandCatalog


@pytest.fixture(autouse=True)
def ensure_qapp(qapp):
    """Ensure a valid QApplication exists for UI tests and restore settings after test."""
    sm = SettingsManager()
    saved_type = sm.get("writing_hand_type", "right")
    saved_style = sm.get("writing_hand_style", "style_01")
    saved_size = sm.get("writing_hand_size", 3.0)
    saved_algo = sm.get("writing_algorithm", "realistic_hybrid")

    yield qapp

    sm.set("writing_hand_type", saved_type)
    sm.set("writing_hand_style", saved_style)
    sm.set("writing_hand_size", saved_size)
    sm.set("writing_algorithm", saved_algo)



def test_drawing_settings_contains_handwriting_card():
    """Verify DrawingSettings contains all required handwriting controls."""
    sm = SettingsManager()
    sm.set("writing_hand_type", "right")
    sm.set("writing_hand_style", "style_01")
    sm.set("writing_hand_size", 3.0)
    sm.set("writing_algorithm", "realistic_hybrid")

    widget = DrawingSettings()

    assert hasattr(widget, "writing_hand_type_combo")
    assert hasattr(widget, "writing_style_combo")
    assert hasattr(widget, "writing_size_slider")
    assert hasattr(widget, "writing_algo_combo")

    # Verify options in hand type combo
    assert widget.writing_hand_type_combo.count() == 2
    assert widget.writing_hand_type_combo.itemText(0) == "Right Hand"
    assert widget.writing_hand_type_combo.itemText(1) == "Left Hand"

    # Verify options in style combo for right hand (Default + 5 models + No Hand)
    assert widget.writing_style_combo.count() == 7
    assert widget.writing_style_combo.currentData() == "style_01"

    # Verify size slider (max 2.0x -> value 20)
    assert widget.writing_size_slider.value() == 20

    # Verify algorithm combo
    assert widget.writing_algo_combo.currentData() == "realistic_hybrid"


def test_drawing_settings_dynamic_style_refresh_on_hand_type_change():
    """Verify changing hand type dynamically reloads available styles and updates settings."""
    sm = SettingsManager()
    widget = DrawingSettings()

    # Switch to Left Hand (index 1)
    widget.writing_hand_type_combo.setCurrentIndex(1)
    assert sm.get("writing_hand_type") == "left"

    # Left styles should now be loaded in the combo
    left_styles = WritingHandCatalog.get_available_styles("left")
    assert widget.writing_style_combo.count() == len(left_styles)

    # Change style to style_03
    idx_03 = widget.writing_style_combo.findData("style_03")
    assert idx_03 >= 0
    widget.writing_style_combo.setCurrentIndex(idx_03)
    assert sm.get("writing_hand_style") == "style_03"


def test_drawing_settings_size_and_algorithm_change():
    """Verify size slider and algorithm combo save to SettingsManager."""
    sm = SettingsManager()
    widget = DrawingSettings()

    # Change size slider to 1.5x (value 15)
    widget.writing_size_slider.setValue(15)
    assert sm.get("writing_hand_size") == 1.5
    assert widget.writing_size_lbl.text() == "1.5x"

    # Change algorithm to two_thirds_power_law
    idx_algo = widget.writing_algo_combo.findData("two_thirds_power_law")
    assert idx_algo >= 0
    widget.writing_algo_combo.setCurrentIndex(idx_algo)
    assert sm.get("writing_algorithm") == "two_thirds_power_law"


def test_live_sync_between_settings_ui_and_writing_hand_item():
    """Verify WritingHandItem reacts immediately when settings are changed through the UI."""
    sm = SettingsManager()
    sm.set("writing_hand_type", "right")
    sm.set("writing_hand_style", "style_01")

    hand_item = WritingHandItem()
    assert hand_item.current_hand_type == "right"
    assert hand_item.current_style_id == "style_01"

    widget = DrawingSettings()

    # Change to Left Hand style_02 via widget
    widget.writing_hand_type_combo.setCurrentIndex(1)  # Left
    idx_02 = widget.writing_style_combo.findData("style_02")
    widget.writing_style_combo.setCurrentIndex(idx_02)

    assert hand_item.current_hand_type == "left"
    assert hand_item.current_style_id == "style_02"
    assert not hand_item.pixmap().isNull()
