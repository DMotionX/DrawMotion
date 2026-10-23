from PySide6.QtCore import QPointF, QRectF
import math
from typing import Dict, Any, Tuple

class MotionSolver:
    """
    Mathematical & Physics solver for motion entrance animations:
    - Hand Drag & Place: realistic human hand holding, placing, settling, and retreating.
    - Directional Slide-In: smooth physics-based translation and fade without hand.
    - Elastic Pop & Scale: playful spring bounce from center.
    """

    @staticmethod
    def ease_smooth(t: float) -> float:
        """Cubic ease-out: starts fast, slows to a gentle halt."""
        t = max(0.0, min(1.0, t))
        return 1.0 - math.pow(1.0 - t, 3.0)

    @staticmethod
    def ease_elastic(t: float) -> float:
        """Damped spring oscillation: subtle realistic rebound settling."""
        t = max(0.0, min(1.0, t))
        if t <= 0.0: return 0.0
        if t >= 1.0: return 1.0
        return math.sin(-13.0 * (t + 1.0) * math.pi / 2.0) * math.pow(2.0, -10.0 * t) + 1.0

    @staticmethod
    def ease_linear(t: float) -> float:
        return max(0.0, min(1.0, t))

    @classmethod
    def get_easing_func(cls, easing_name: str):
        easing_name = (easing_name or "smooth").lower()
        if "elastic" in easing_name or "bounc" in easing_name:
            return cls.ease_elastic
        elif "linear" in easing_name:
            return cls.ease_linear
        return cls.ease_smooth

    @staticmethod
    def compute_entry_start_pos(direction: str, artboard_rect: QRectF, item_rect: QRectF, target_pos: QPointF, item_scale: float = 1.0) -> QPointF:
        """
        Calculates the off-screen start position based on entry direction and artboard bounds.
        Guarantees the item starts completely invisible beyond the canvas border.
        """
        w = item_rect.width() * item_scale
        h = item_rect.height() * item_scale
        margin = 100.0

        dir_clean = (direction or "left").lower()
        if "right" in dir_clean:
            start_x = artboard_rect.right() + margin
            start_y = target_pos.y()
        elif "top" in dir_clean:
            start_x = target_pos.x()
            start_y = artboard_rect.top() - h - margin
        elif "bottom" in dir_clean:
            start_x = target_pos.x()
            start_y = artboard_rect.bottom() + margin
        else: # Default: Left
            start_x = artboard_rect.left() - w - margin
            start_y = target_pos.y()

        return QPointF(start_x, start_y)

    @classmethod
    def solve_frame(cls, 
                    time_in_item: float, 
                    motion_duration: float, 
                    motion_style: str, 
                    direction: str, 
                    easing: str,
                    target_pos: QPointF, 
                    item_rect: QRectF, 
                    item_scale: float, 
                    artboard_rect: QRectF) -> Dict[str, Any]:
        """
        Solves item and hand properties for a given instant in time.
        
        Returns:
            {
                "item_pos": QPointF,
                "item_scale_mult": float,
                "item_opacity": float,
                "item_rotation_offset": float,
                "hand_visible": bool,
                "hand_pos": QPointF,
                "hand_scale": float
            }
        """
        motion_style = (motion_style or "hand_drag").lower()
        motion_duration = max(0.4, float(motion_duration or 1.5))
        easing_fn = cls.get_easing_func(easing)

        # Before start: hidden off-screen
        if time_in_item < 0.0:
            start_pos = cls.compute_entry_start_pos(direction, artboard_rect, item_rect, target_pos, item_scale)
            return {
                "item_pos": start_pos,
                "item_scale_mult": 1.0,
                "item_opacity": 0.0,
                "item_rotation_offset": 0.0,
                "hand_visible": False,
                "hand_pos": start_pos,
                "hand_scale": 1.0
            }

        # ---------------------------------------------------------
        # STYLE 1: Hand Drag & Place
        # ---------------------------------------------------------
        if "hand" in motion_style or "drag" in motion_style:
            start_pos = cls.compute_entry_start_pos(direction, artboard_rect, item_rect, target_pos, item_scale)
            
            # Proportional timeline division:
            # Phase 1A: Entrance Travel (0.0 to 65% of motion_duration)
            travel_dur = motion_duration * 0.65
            # Phase 1B: Settle / Release (65% to 80% of motion_duration)
            settle_dur = motion_duration * 0.15
            # Phase 1C: Hand Retreat out of screen (80% to 100% of motion_duration)
            retreat_dur = motion_duration * 0.20
            
            w = item_rect.width() * item_scale
            h = item_rect.height() * item_scale
            # Hand holding anchor calibrated for hand_drag.png (gripping top-right edge)
            grip_offset_x = w * 0.75
            grip_offset_y = min(25.0, h * 0.1)
            
            if time_in_item <= travel_dur:
                progress = time_in_item / travel_dur if travel_dur > 0 else 1.0
                eased = easing_fn(progress)
                curr_x = start_pos.x() + (target_pos.x() - start_pos.x()) * eased
                curr_y = start_pos.y() + (target_pos.y() - start_pos.y()) * eased
                curr_pos = QPointF(curr_x, curr_y)
                
                hand_pos = QPointF(curr_x + grip_offset_x, curr_y + grip_offset_y)
                return {
                    "item_pos": curr_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": True,
                    "hand_pos": hand_pos,
                    "hand_scale": 1.0
                }
                
            elif time_in_item <= travel_dur + settle_dur:
                # Settle phase: Item is in final position; hand lingers and releases
                hand_pos = QPointF(target_pos.x() + grip_offset_x, target_pos.y() + grip_offset_y)
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": True,
                    "hand_pos": hand_pos,
                    "hand_scale": 1.0
                }
                
            elif time_in_item <= motion_duration:
                # Retreat phase: Item stays, hand retreats smoothly towards off-screen corner
                retreat_t = (time_in_item - (travel_dur + settle_dur)) / retreat_dur if retreat_dur > 0 else 1.0
                eased_retreat = cls.ease_smooth(retreat_t)
                
                grip_x = target_pos.x() + grip_offset_x
                grip_y = target_pos.y() + grip_offset_y
                # Retreat direction: towards bottom-right edge
                retreat_target_x = grip_x + 500.0
                retreat_target_y = grip_y + 400.0
                
                curr_hx = grip_x + (retreat_target_x - grip_x) * eased_retreat
                curr_hy = grip_y + (retreat_target_y - grip_y) * eased_retreat
                
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": True,
                    "hand_pos": QPointF(curr_hx, curr_hy),
                    "hand_scale": 1.0
                }
            else:
                # Static hold: Item at target, hand hidden
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0
                }

        # ---------------------------------------------------------
        # STYLE 2: Directional Slide-In (No hand)
        # ---------------------------------------------------------
        elif "slide" in motion_style:
            start_pos = cls.compute_entry_start_pos(direction, artboard_rect, item_rect, target_pos, item_scale)
            slide_dur = motion_duration * 0.75
            if time_in_item <= slide_dur:
                progress = time_in_item / slide_dur if slide_dur > 0 else 1.0
                eased = easing_fn(progress)
                curr_x = start_pos.x() + (target_pos.x() - start_pos.x()) * eased
                curr_y = start_pos.y() + (target_pos.y() - start_pos.y()) * eased
                opacity = min(1.0, max(0.0, progress * 1.5))
                return {
                    "item_pos": QPointF(curr_x, curr_y),
                    "item_scale_mult": 1.0,
                    "item_opacity": opacity,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0
                }
            else:
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0
                }

        # ---------------------------------------------------------
        # STYLE 3: Elastic Pop & Scale (Spring bounce from center)
        # ---------------------------------------------------------
        else: # elastic_pop
            w = item_rect.width() * item_scale
            h = item_rect.height() * item_scale
            pop_dur = motion_duration * 0.75
            if time_in_item <= pop_dur:
                progress = time_in_item / pop_dur if pop_dur > 0 else 1.0
                eased = cls.ease_elastic(progress)
                opacity = min(1.0, max(0.0, progress * 2.0))
                scale_mult = max(0.001, eased)
                # Keep center pinned so it pops outward from middle
                curr_x = target_pos.x() + (w * (1.0 - scale_mult) * 0.5)
                curr_y = target_pos.y() + (h * (1.0 - scale_mult) * 0.5)
                return {
                    "item_pos": QPointF(curr_x, curr_y),
                    "item_scale_mult": scale_mult,
                    "item_opacity": opacity,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0
                }
            else:
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0
                }
