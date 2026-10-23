from PySide6.QtCore import QPointF, QRectF
from typing import Dict, Any, Optional
from .motion_solver import MotionSolver

class MotionEngine:
    """
    Central motion engine coordinator:
    - Applies entrance motion to canvas items during live preview and export.
    - Manages original item transformations safely to eliminate drift and ensure zero regressions.
    """

    @classmethod
    def capture_target_transform(cls, item):
        """Captures the live user transform as the design target."""
        item._motion_target_pos = QPointF(item.pos().x(), item.pos().y())
        item._motion_target_scale = float(item.scale())
        item._motion_target_opacity = float(item.opacity())
        item._motion_target_rotation = float(item.rotation())

    @classmethod
    def ensure_item_motion_cached(cls, item, force_refresh=False):
        """Caches the user's intended target transform (final scene position)."""
        if force_refresh or not hasattr(item, '_motion_target_pos'):
            cls.capture_target_transform(item)

    @staticmethod
    def reset_item(item):
        """Restores the item to its user-edited design-time target transform."""
        if hasattr(item, '_motion_target_pos'):
            item.setPos(item._motion_target_pos)
            item.setScale(item._motion_target_scale)
            item.setOpacity(item._motion_target_opacity)
            item.setRotation(item._motion_target_rotation)

    @classmethod
    def apply_motion_frame(cls,
                           item,
                           hand_item,
                           time_sec: float,
                           start_time: float,
                           action_duration: float,
                           artboard_rect: QRectF,
                           hand_size_setting: float = 3.0) -> bool:
        """
        Calculates and applies the motion transform for the given time.
        
        Returns:
            bool: True if motion was applied successfully.
        """
        cls.ensure_item_motion_cached(item)

        time_in_item = time_sec - start_time
        settings = getattr(item, 'motion_settings', {}) or {}
        
        motion_style = settings.get("style", "hand_drag")
        direction = settings.get("direction", "left")
        
        # Seamless timeline synchronization: adapt motion duration to block duration
        if action_duration > 0:
            motion_dur = action_duration
        else:
            motion_dur = float(settings.get("duration", 1.5))
            
        easing = settings.get("easing", "smooth")

        target_pos = item._motion_target_pos
        item_rect = item.boundingRect()
        base_scale = item._motion_target_scale

        solution = MotionSolver.solve_frame(
            time_in_item=time_in_item,
            motion_duration=motion_dur,
            motion_style=motion_style,
            direction=direction,
            easing=easing,
            target_pos=target_pos,
            item_rect=item_rect,
            item_scale=base_scale,
            artboard_rect=artboard_rect
        )

        # 1. Apply transform to the item
        item.setPos(solution["item_pos"])
        item.setScale(base_scale * solution["item_scale_mult"])
        item.setOpacity(item._motion_target_opacity * solution["item_opacity"])
        
        # Ensure image shows 100% full pixmap (no vector draw mask)
        if hasattr(item, 'set_progress'):
            item.set_progress(1.0)

        # 2. Apply hand state
        if hand_item:
            if solution["hand_visible"] and time_in_item >= 0.0:
                hand_item.show()
                if hasattr(hand_item, 'set_drag_mode'):
                    hand_item.set_drag_mode(True)
                if hasattr(hand_item, 'set_ink_active'):
                    hand_item.set_ink_active(False)
                    
                from core.settings_manager import SettingsManager
                try:
                    drag_hand_size = float(SettingsManager().get("drag_hand_size", 1.0))
                except (ValueError, TypeError):
                    drag_hand_size = 1.0
                    
                # Balanced natural scale: proportioned relative to the item scale
                proportional_factor = max(0.5, min(2.5, base_scale))
                hand_item.setScale(drag_hand_size * proportional_factor)
                hand_item.setPos(solution["hand_pos"])
            else:
                hand_item.hide()
                if hasattr(hand_item, 'set_ink_active'):
                    hand_item.set_ink_active(False)

        return True
