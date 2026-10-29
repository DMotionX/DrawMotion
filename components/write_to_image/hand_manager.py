"""
Dedicated Writing Hand Item & Manager for the Text Writing Engine.
Provides isolated QGraphicsPixmapItem lifecycle, sub-pixel tip anchoring,
and seamless integration with WritingHandCatalog and SettingsManager.
"""

from typing import Optional, Any
from PySide6.QtWidgets import QGraphicsPixmapItem
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QPointF
from core.settings_manager import SettingsManager
from .hand_catalog import WritingHandCatalog, DEFAULT_HAND_TYPE, DEFAULT_STYLE_ID


class WritingHandItem(QGraphicsPixmapItem):
    """
    Dedicated QGraphicsPixmapItem specifically for text handwriting animations.
    Decoupled completely from whiteboard drawing HandItem to eliminate regression risks.
    """
    BASE_RENDER_WIDTH = 500  # Standard crisp texture width for 60 FPS rendering

    def __init__(self, scene=None):
        super().__init__()
        self.setZValue(9999)  # Keep writing hand above all canvas items
        self.hide()

        self.current_hand_type = DEFAULT_HAND_TYPE
        self.current_style_id = DEFAULT_STYLE_ID
        self._last_item = None

        if scene is not None:
            scene.addItem(self)

        # Connect to settings changes for live reactive update
        self._sm = SettingsManager()
        self._sm.settings_changed.connect(self._on_setting_changed)

        self.reload_hand()

    def _on_setting_changed(self, key: str, value: Any):
        if key in ("writing_hand_type", "writing_hand_style", "writing_hand_size"):
            self.reload_hand()

    def reload_hand(self):
        """Reloads the active writing hand model and tip offset from settings."""
        hand_type = self._sm.get("writing_hand_type", DEFAULT_HAND_TYPE)
        style_id = self._sm.get("writing_hand_style", DEFAULT_STYLE_ID)
        self.set_hand(hand_type, style_id)
        if self._last_item is not None:
            self.update_item_scale(self._last_item)

    def set_hand(self, hand_type: str, style_id: str):
        """
        Loads the selected writing hand from catalog, scales to base width,
        and applies mathematically calibrated zero-drift tip offset.
        """
        self.current_hand_type = WritingHandCatalog.normalize_hand_type(hand_type)
        self.current_style_id = WritingHandCatalog.normalize_style_id(style_id)

        if self.current_style_id == "none":
            self.setPixmap(QPixmap())
            self.setOffset(0.0, 0.0)
            self.hide()
            return

        raw_pixmap = WritingHandCatalog.get_pixmap(self.current_hand_type, self.current_style_id)
        if raw_pixmap is None or raw_pixmap.isNull():
            self.hide()
            return

        # Pre-scale to standard width for silky smooth GPU rendering without texture stutter
        scaled_pixmap = raw_pixmap.scaledToWidth(
            self.BASE_RENDER_WIDTH,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)

        # Calculate exact tip offset relative to scaled pixmap
        scale_ratio = self.BASE_RENDER_WIDTH / float(raw_pixmap.width())
        tip_offset = WritingHandCatalog.get_tip_offset(
            self.current_hand_type,
            self.current_style_id,
            scale=scale_ratio
        )
        self.setOffset(tip_offset)

    def get_rendered_scene_width(self) -> float:
        """Returns the current rendered width of the writing hand in scene units."""
        return float(self.BASE_RENDER_WIDTH) * self.scale()

    def update_item_scale(self, item=None):
        """
        Computes dynamic hand scale strictly decoupled from whiteboard hand_size.
        Scales with ergonomic anthropomorphic calibration in scene space,
        ensuring natural visual parity across all languages (English & Arabic)
        and responsive adaptation when resizing text items.
        """
        if item is not None:
            self._last_item = item
        elif self._last_item is not None:
            item = self._last_item

        try:
            user_mult = float(self._sm.get("writing_hand_size", 1.0))
        except (ValueError, TypeError):
            user_mult = 1.0

        # Per-item override if present on model
        if item is not None and hasattr(item, 'model') and hasattr(item.model, 'writing_hand_size'):
            try:
                user_mult = float(item.model.writing_hand_size)
            except (ValueError, TypeError):
                pass

        # Scene-Space Ergonomic Base: natural human hand holding pen on 1080p canvas (~360px - 400px)
        BASE_SCENE_HAND_WIDTH = 370.0

        item_scale = 1.0
        line_h = 32.0

        if item is not None:
            item_scale = max(0.1, float(item.scale()))
            if hasattr(item, 'model') and getattr(item.model, 'font_size', None):
                line_h = float(item.model.font_size) * 1.33
            elif hasattr(item, 'boundingRect'):
                h = item.boundingRect().height()
                if h > 10.0:
                    line_h = min(h, 90.0)

        # Scene-space line height: how large the text glyphs actually appear on the screen
        scene_line_h = line_h * item_scale

        # Dynamic scale factor based on scene line height relative to baseline (32px * 1.0)
        # Moderate growth so large headlines slightly enlarge the hand,
        # but smaller body text never shrinks the human hand into a miniature doll.
        # Baseline reference line height: 32.0 px (standard 24pt text at 1.0 scale)
        ref_line_h = 32.0
        ratio = max(0.5, scene_line_h / ref_line_h)
        dyn_factor = 1.0 + 0.15 * (ratio - 1.0)

        # Target hand width in scene coordinates
        target_scene_w = BASE_SCENE_HAND_WIDTH * user_mult * dyn_factor

        # Clamp to realistic ergonomic boundaries [280px * user_mult, 520px * user_mult]
        min_w = 280.0 * user_mult
        max_w = 520.0 * user_mult
        bounded_scene_w = max(min_w, min(target_scene_w, max_w))

        # Convert to QGraphicsItem scale (BASE_RENDER_WIDTH = 500.0)
        final_scale = bounded_scene_w / float(self.BASE_RENDER_WIDTH)
        self.setScale(final_scale)

    def update_position(self, scene_tip_pos: QPointF, item=None, is_writing: bool = True):
        """
        Updates hand position and visibility for the current animation frame.
        Because tip_offset aligns the pen tip to local (0, 0), pos() places the tip exactly on scene_tip_pos.
        """
        if item is not None and hasattr(item, 'model'):
            target_ht = getattr(item.model, 'writing_hand_type', None) or self._sm.get("writing_hand_type", DEFAULT_HAND_TYPE)
            target_sid = getattr(item.model, 'writing_hand_style', None) or self._sm.get("writing_hand_style", DEFAULT_STYLE_ID)
            norm_ht = WritingHandCatalog.normalize_hand_type(target_ht)
            norm_sid = WritingHandCatalog.normalize_style_id(target_sid)
            if norm_ht != self.current_hand_type or norm_sid != self.current_style_id:
                self.set_hand(norm_ht, norm_sid)

        if self.current_style_id == "none":
            self.hide()
            return

        if item is not None:
            self.update_item_scale(item)

        self.setPos(scene_tip_pos)

        if is_writing:
            if not self.isVisible():
                self.show()
        else:
            self.hide()


class TextHandManager:
    """
    Backward-compatible wrapper preserving legacy TextHandManager interface.
    """
    def __init__(self, scene=None):
        self.scene = scene
        self.hand_item = WritingHandItem(scene=scene)
        self.is_active = False

    def update_position(self, scene_pos: QPointF, is_drawing: bool):
        self.hand_item.update_position(scene_pos, is_writing=is_drawing)
        self.is_active = self.hand_item.isVisible()

    def remove(self):
        if self.scene and self.hand_item in self.scene.items():
            self.scene.removeItem(self.hand_item)
