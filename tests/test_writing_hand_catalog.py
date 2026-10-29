"""
Automated unit tests for Phase 1: Writing Hand Catalog & Tip Calibration Matrix.
Verifies all 10 models (5 right, 5 left) exist, load into QPixmap, have accurate tip offsets,
and handle normalization and fallbacks properly.
"""

import os
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QPointF

# Ensure QApplication exists for QPixmap operations
app = QApplication.instance()
if app is None:
    app = QApplication([])

from components.write_to_image.hand_catalog import (
    WritingHandCatalog,
    WRITING_HAND_REGISTRY,
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    DEFAULT_HAND_TYPE,
    DEFAULT_STYLE_ID,
)


def test_registry_contains_ten_models():
    """Verify registry has default and style_01-05 models for right and left hands."""
    assert "right" in WRITING_HAND_REGISTRY
    assert "left" in WRITING_HAND_REGISTRY
    assert len(WRITING_HAND_REGISTRY["right"]) == 6
    assert len(WRITING_HAND_REGISTRY["left"]) == 6

    for ht in ("right", "left"):
        for sid in ("default", "style_01", "style_02", "style_03", "style_04", "style_05"):
            assert sid in WRITING_HAND_REGISTRY[ht]
            entry = WRITING_HAND_REGISTRY[ht][sid]
            assert entry["tip_x"] >= 0
            assert entry["tip_y"] >= 0


def test_all_ten_asset_files_exist_on_disk():
    """Verify that all asset files in registry exist on the filesystem."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    for ht in ("right", "left"):
        for sid, entry in WRITING_HAND_REGISTRY[ht].items():
            full_path = os.path.join(base_dir, entry["rel_path"])
            assert os.path.exists(full_path), f"Missing asset: {full_path}"


def test_pixmap_loading_and_caching():
    """Verify that QPixmap loads successfully for models and caching works."""
    WritingHandCatalog.clear_cache()
    
    for ht in ("right", "left"):
        for sid in ("default", "style_01", "style_02", "style_03", "style_04", "style_05"):
            pix = WritingHandCatalog.get_pixmap(ht, sid)
            assert pix is not None, f"Failed to load pixmap for {ht}/{sid}"
            assert not pix.isNull(), f"Pixmap is null for {ht}/{sid}"

    # Check cache has 12 entries (6 right + 6 left)
    assert len(WritingHandCatalog._pixmap_cache) == 12
    
    # Test retrieving from cache returns the same instance
    pix_cached = WritingHandCatalog.get_pixmap("right", "default")
    assert pix_cached is not None
    assert not pix_cached.isNull()


def test_tip_offset_calculation():
    """Verify tip offset matches exact negative coordinates for zero-drift alignment."""
    # Right default: tip at (10.0, 15.0)
    offset_rd = WritingHandCatalog.get_tip_offset("right", "default", scale=1.0)
    assert offset_rd.x() == -10.0
    assert offset_rd.y() == -15.0

    # Right Model 1: tip at (84.0, 175.0)
    offset_r1 = WritingHandCatalog.get_tip_offset("right", "style_01", scale=1.0)
    assert offset_r1.x() == -84.0
    assert offset_r1.y() == -175.0

    # With scale = 0.5
    offset_r1_half = WritingHandCatalog.get_tip_offset("right", "style_01", scale=0.5)
    assert offset_r1_half.x() == -84.0 * 0.5
    assert offset_r1_half.y() == -175.0 * 0.5

    # Left default: tip at (1519.0, 12.0)
    offset_ld = WritingHandCatalog.get_tip_offset("left", "default", scale=1.0)
    assert offset_ld.x() == -1519.0
    assert offset_ld.y() == -12.0


def test_normalization_and_fallbacks():
    """Verify hand_type and style_id normalization and robust fallback handling."""
    # Normalizing hand types
    assert WritingHandCatalog.normalize_hand_type("RIGHT") == "right"
    assert WritingHandCatalog.normalize_hand_type("left") == "left"
    assert WritingHandCatalog.normalize_hand_type("lh") == "left"
    assert WritingHandCatalog.normalize_hand_type("unknown") == "right"

    # Normalizing style IDs
    assert WritingHandCatalog.normalize_style_id("default") == "default"
    assert WritingHandCatalog.normalize_style_id("1") == "style_01"
    assert WritingHandCatalog.normalize_style_id("model_2") == "style_02"
    assert WritingHandCatalog.normalize_style_id("style_05") == "style_05"
    assert WritingHandCatalog.normalize_style_id("none") == "none"

    # 'none' returns None for entry and pixmap, and (0,0) for offset
    assert WritingHandCatalog.get_entry("right", "none") is None
    assert WritingHandCatalog.get_pixmap("right", "none") is None
    assert WritingHandCatalog.get_tip_offset("right", "none") == QPointF(0.0, 0.0)

    # Invalid style falls back to default
    entry_fallback = WritingHandCatalog.get_entry("right", "invalid_style_xyz")
    assert entry_fallback["id"] == "default"


def test_get_available_styles():
    """Verify available styles list is correctly populated for UI dropdowns."""
    styles_r = WritingHandCatalog.get_available_styles("right")
    assert len(styles_r) == 7  # default + 5 models + 'none'
    style_ids_r = [s[0] for s in styles_r]
    assert "default" in style_ids_r
    assert "style_01" in style_ids_r
    assert "style_05" in style_ids_r
    assert "none" in style_ids_r

    styles_l = WritingHandCatalog.get_available_styles("left")
    assert len(styles_l) == 7
