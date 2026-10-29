"""
Writing Hand Catalog & Tip Calibration Matrix.
Provides calibrated tip offsets, asset path resolution, and cached pixmap loading
for the 10 dedicated 3D cartoon writing hand models (5 right, 5 left).
"""

import os
from typing import Dict, Any, Optional, List, Tuple
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QPointF
from utils.paths import resource_path

# Calibrated Native Dimensions for all writepen assets: 1536 x 2304
NATIVE_WIDTH = 1536
NATIVE_HEIGHT = 2304

# Full calibrated registry of all 10 writing hand models
# Tip coordinates were mathematically measured on non-transparent alpha bounds
WRITING_HAND_REGISTRY: Dict[str, Dict[str, Dict[str, Any]]] = {
    "right": {
        "default": {
            "id": "default",
            "name": "Default Hand (Optimized)",
            "rel_path": os.path.join("assets", "writepen", "hand_right_default.png"),
            "tip_x": 10.0,
            "tip_y": 15.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
        "style_01": {
            "id": "style_01",
            "name": "Model 1 - Classic Coral",
            "rel_path": os.path.join("assets", "writepen", "right", "hand_rtl_01.png"),
            "tip_x": 84.0,
            "tip_y": 175.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
        "style_02": {
            "id": "style_02",
            "name": "Model 2 - Amber Gold",
            "rel_path": os.path.join("assets", "writepen", "right", "handrtl_02.png"),
            "tip_x": 107.0,
            "tip_y": 229.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
        "style_03": {
            "id": "style_03",
            "name": "Model 3 - Warm Crimson",
            "rel_path": os.path.join("assets", "writepen", "right", "handrtl_03.png"),
            "tip_x": 136.0,
            "tip_y": 171.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
        "style_04": {
            "id": "style_04",
            "name": "Model 4 - Terracotta",
            "rel_path": os.path.join("assets", "writepen", "right", "hand_rtl_04.png"),
            "tip_x": 107.0,
            "tip_y": 212.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
        "style_05": {
            "id": "style_05",
            "name": "Model 5 - Peach Rose",
            "rel_path": os.path.join("assets", "writepen", "right", "hand_rtl_05.png"),
            "tip_x": 107.0,
            "tip_y": 132.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
    },
    "left": {
        "default": {
            "id": "default",
            "name": "Default Hand (Optimized)",
            "rel_path": os.path.join("assets", "writepen", "hand_left_default.png"),
            "tip_x": 1519.0,
            "tip_y": 12.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
        "style_01": {
            "id": "style_01",
            "name": "Model 1 - Classic Coral",
            "rel_path": os.path.join("assets", "writepen", "left", "hand_action_01.png"),
            "tip_x": 1439.0,
            "tip_y": 260.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
        "style_02": {
            "id": "style_02",
            "name": "Model 2 - Amber Gold",
            "rel_path": os.path.join("assets", "writepen", "left", "hand_action_02.png"),
            "tip_x": 1438.0,
            "tip_y": 278.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
        "style_03": {
            "id": "style_03",
            "name": "Model 3 - Warm Crimson",
            "rel_path": os.path.join("assets", "writepen", "left", "hand_action_03.png"),
            "tip_x": 1402.0,
            "tip_y": 268.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
        "style_04": {
            "id": "style_04",
            "name": "Model 4 - Terracotta",
            "rel_path": os.path.join("assets", "writepen", "left", "hand_action_04.png"),
            "tip_x": 1443.0,
            "tip_y": 298.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
        "style_05": {
            "id": "style_05",
            "name": "Model 5 - Peach Rose",
            "rel_path": os.path.join("assets", "writepen", "left", "hand_action_05.png"),
            "tip_x": 1433.0,
            "tip_y": 242.0,
            "width": NATIVE_WIDTH,
            "height": NATIVE_HEIGHT,
        },
    }
}

DEFAULT_HAND_TYPE = "right"
DEFAULT_STYLE_ID = "default"


class WritingHandCatalog:
    """
    Central repository and cache for writing hand assets and tip calibration.
    """
    _pixmap_cache: Dict[str, QPixmap] = {}

    @classmethod
    def normalize_hand_type(cls, hand_type: str) -> str:
        """Normalizes hand type string to 'right' or 'left'."""
        ht = str(hand_type).lower().strip()
        if ht in ("left", "lh", "rtl_left"):
            return "left"
        return "right"

    @classmethod
    def normalize_style_id(cls, style_id: str) -> str:
        """Normalizes style ID to valid format (e.g. default, style_01)."""
        sid = str(style_id).lower().strip()
        if sid in ("none", "disabled", "off"):
            return "none"
        if sid in ("default", "std", "standard", "normal", "main"):
            return "default"
        if sid in ("1", "01", "model1", "model_1", "style_1", "style_01"):
            return "style_01"
        if sid in ("2", "02", "model2", "model_2", "style_2", "style_02"):
            return "style_02"
        if sid in ("3", "03", "model3", "model_3", "style_3", "style_03"):
            return "style_03"
        if sid in ("4", "04", "model4", "model_4", "style_4", "style_04"):
            return "style_04"
        if sid in ("5", "05", "model5", "model_5", "style_5", "style_05"):
            return "style_05"
        return DEFAULT_STYLE_ID

    @classmethod
    def get_entry(cls, hand_type: str = DEFAULT_HAND_TYPE, style_id: str = DEFAULT_STYLE_ID) -> Optional[Dict[str, Any]]:
        """
        Retrieves calibration metadata entry for specified hand type and style.
        Returns None if style is 'none'.
        """
        norm_type = cls.normalize_hand_type(hand_type)
        norm_style = cls.normalize_style_id(style_id)
        
        if norm_style == "none":
            return None
            
        type_dict = WRITING_HAND_REGISTRY.get(norm_type, WRITING_HAND_REGISTRY[DEFAULT_HAND_TYPE])
        entry = type_dict.get(norm_style)
        if entry is None:
            entry = type_dict.get(DEFAULT_STYLE_ID)
        return entry

    @classmethod
    def get_pixmap(cls, hand_type: str = DEFAULT_HAND_TYPE, style_id: str = DEFAULT_STYLE_ID) -> Optional[QPixmap]:
        """
        Loads and caches QPixmap for the specified writing hand.
        """
        entry = cls.get_entry(hand_type, style_id)
        if entry is None:
            return None
            
        rel_path = entry["rel_path"]
        if rel_path in cls._pixmap_cache and not cls._pixmap_cache[rel_path].isNull():
            return cls._pixmap_cache[rel_path]
            
        full_path = resource_path(rel_path)
        if not os.path.exists(full_path):
            # Fallback path check relative to project root
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            full_path = os.path.join(base_dir, rel_path)

        pixmap = QPixmap(full_path)
        if not pixmap.isNull():
            cls._pixmap_cache[rel_path] = pixmap
            return pixmap
            
        return None

    @classmethod
    def get_tip_offset(cls, hand_type: str = DEFAULT_HAND_TYPE, style_id: str = DEFAULT_STYLE_ID, scale: float = 1.0) -> QPointF:
        """
        Calculates QGraphicsPixmapItem offset (-tip_x * scale, -tip_y * scale)
        so that when pos() is set to target ink point, the tip perfectly hits it.
        """
        entry = cls.get_entry(hand_type, style_id)
        if entry is None:
            return QPointF(0.0, 0.0)
            
        tip_x = float(entry["tip_x"]) * scale
        tip_y = float(entry["tip_y"]) * scale
        return QPointF(-tip_x, -tip_y)

    @classmethod
    def get_available_styles(cls, hand_type: str = DEFAULT_HAND_TYPE) -> List[Tuple[str, str]]:
        """
        Returns list of (style_id, name) tuples for UI dropdown population.
        """
        norm_type = cls.normalize_hand_type(hand_type)
        type_dict = WRITING_HAND_REGISTRY.get(norm_type, WRITING_HAND_REGISTRY[DEFAULT_HAND_TYPE])
        styles = [(k, v["name"]) for k, v in type_dict.items()]
        styles.append(("none", "No Hand"))
        return styles

    @classmethod
    def clear_cache(cls):
        """Clears cached QPixmaps."""
        cls._pixmap_cache.clear()
