# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
from PySide6.QtCore import QPointF, QRectF
import math
from typing import Dict, Any, Tuple

class MotionSolver:
    """
    Mathematical & Physics solver for motion entrance animations in DrawMotion Studio.
    Supports 8-directional entry matrix, realistic hand mechanics, and 8 motion styles:
    - Hand Drag & Place: realistic human hand grip, placement, settle, and retreat.
    - Hand Push & Slide: human hand pushing the object from behind along the canvas.
    - Directional Slide-In: smooth physics translation and fade without hand.
    - Gravity Drop & Bounce: realistic acceleration fall with physical ground bounce.
    - Elastic Pop & Scale: playful spring bounce from center.
    - 3D Flip Card: card flip perspective reveal around vertical/horizontal axis.
    - Cinematic Zoom: smooth focal scale-in with opacity focus.
    - Arc Glide: sweeping curved Bezier trajectory into final placement.
    """

    @staticmethod
    def ease_smooth(t: float) -> float:
        """Smooth hermite ease-in-out: gentle start, natural travel, smooth deceleration."""
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def ease_elastic(t: float) -> float:
        """Damped spring oscillation: subtle realistic rebound settling."""
        t = max(0.0, min(1.0, t))
        if t <= 0.0: return 0.0
        if t >= 1.0: return 1.0
        return math.sin(-13.0 * (t + 1.0) * math.pi / 2.0) * math.pow(2.0, -10.0 * t) + 1.0

    @staticmethod
    def ease_bounce(t: float) -> float:
        """Physical ground bounce curve."""
        t = max(0.0, min(1.0, t))
        n1 = 7.5625
        d1 = 2.75
        if t < 1.0 / d1:
            return n1 * t * t
        elif t < 2.0 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375

    @staticmethod
    def ease_back(t: float) -> float:
        """Overshoot / anticipation ease-out."""
        t = max(0.0, min(1.0, t))
        c1 = 1.70158
        c3 = c1 + 1.0
        return 1.0 + c3 * math.pow(t - 1.0, 3) + c1 * math.pow(t - 1.0, 2)

    @staticmethod
    def ease_exponential(t: float) -> float:
        """Fast start, smooth cinematic deceleration brake."""
        t = max(0.0, min(1.0, t))
        return 1.0 if t >= 1.0 else 1.0 - math.pow(2.0, -10.0 * t)

    @staticmethod
    def ease_linear(t: float) -> float:
        return max(0.0, min(1.0, t))

    @classmethod
    def get_easing_func(cls, easing_name: str):
        easing_name = (easing_name or "smooth").lower()
        if "elastic" in easing_name:
            return cls.ease_elastic
        elif "bounc" in easing_name:
            return cls.ease_bounce
        elif "back" in easing_name:
            return cls.ease_back
        elif "expo" in easing_name:
            return cls.ease_exponential
        elif "linear" in easing_name:
            return cls.ease_linear
        return cls.ease_smooth

    @classmethod
    def get_easing_function(cls, easing_name: str):
        return cls.get_easing_func(easing_name)

    @staticmethod
    def compute_entry_start_pos(direction: str, artboard_rect: QRectF, item_rect: QRectF, target_pos: QPointF, item_scale: float = 1.0) -> QPointF:
        """
        Calculates the off-screen start position across all 8 cardinal and diagonal directions.
        Guarantees both the item and the placement hand start completely invisible beyond canvas borders.
        """
        w = item_rect.width() * item_scale
        h = item_rect.height() * item_scale
        hand_margin_x = max(750.0, w)
        hand_margin_y = max(500.0, h)

        dir_clean = (direction or "left").lower().replace("-", "_").replace(" ", "_")
        
        # 1. Diagonals
        if "top_left" in dir_clean:
            start_x = artboard_rect.left() - w - hand_margin_x
            start_y = artboard_rect.top() - h - hand_margin_y
        elif "top_right" in dir_clean:
            start_x = artboard_rect.right() + hand_margin_x
            start_y = artboard_rect.top() - h - hand_margin_y
        elif "bottom_left" in dir_clean:
            start_x = artboard_rect.left() - w - hand_margin_x
            start_y = artboard_rect.bottom() + hand_margin_y
        elif "bottom_right" in dir_clean:
            start_x = artboard_rect.right() + hand_margin_x
            start_y = artboard_rect.bottom() + hand_margin_y
        # 2. Cardinals
        elif "right" in dir_clean:
            start_x = artboard_rect.right() + hand_margin_x
            start_y = target_pos.y()
        elif "top" in dir_clean:
            start_x = target_pos.x()
            start_y = artboard_rect.top() - h - hand_margin_y
        elif "bottom" in dir_clean:
            start_x = target_pos.x()
            start_y = artboard_rect.bottom() + hand_margin_y
        else: # Default: Left
            start_x = artboard_rect.left() - w - hand_margin_x
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
                "hand_scale": float,
                "sfx_hint": Optional[str]
            }
        """
        motion_style = (motion_style or "hand_drag").lower()
        motion_duration = max(0.4, float(motion_duration or 1.5))
        easing_fn = cls.get_easing_func(easing)

        w = item_rect.width() * item_scale
        h = item_rect.height() * item_scale

        # Hidden state prior to start
        if time_in_item < 0.0:
            start_pos = cls.compute_entry_start_pos(direction, artboard_rect, item_rect, target_pos, item_scale)
            return {
                "item_pos": start_pos,
                "item_scale_mult": 1.0,
                "item_opacity": 0.0,
                "item_rotation_offset": 0.0,
                "hand_visible": False,
                "hand_pos": start_pos,
                "hand_scale": 1.0,
                "sfx_hint": None
            }

        # ---------------------------------------------------------
        # STYLE 1: Hand Drag & Place
        # ---------------------------------------------------------
        if "hand_drag" in motion_style or "drag" in motion_style:
            start_pos = cls.compute_entry_start_pos(direction, artboard_rect, item_rect, target_pos, item_scale)
            travel_dur = motion_duration * 0.85
            settle_dur = motion_duration * 0.07
            retreat_dur = motion_duration * 0.08
            
            dir_clean = (direction or "left").lower().replace("-", "_")
            if "right" in dir_clean and "top" not in dir_clean and "bottom" not in dir_clean:
                grip_offset_x = max(30.0, min(w * 0.25, 80.0))
                grip_offset_y = max(15.0, min(35.0, h * 0.08))
            elif "top" in dir_clean or "bottom" in dir_clean:
                grip_offset_x = w * 0.50
                grip_offset_y = max(15.0, min(35.0, h * 0.08))
            else:
                grip_offset_x = max(30.0, min(w - 30.0, w * 0.65))
                grip_offset_y = max(15.0, min(35.0, h * 0.08))

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
                    "hand_scale": 1.0,
                    "sfx_hint": "whoosh" if progress < 0.2 else None
                }
            elif time_in_item <= travel_dur + settle_dur:
                hand_pos = QPointF(target_pos.x() + grip_offset_x, target_pos.y() + grip_offset_y)
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": True,
                    "hand_pos": hand_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": "impact"
                }
            elif time_in_item <= motion_duration:
                retreat_t = (time_in_item - (travel_dur + settle_dur)) / retreat_dur if retreat_dur > 0 else 1.0
                eased_retreat = retreat_t * retreat_t
                grip_x = target_pos.x() + grip_offset_x
                grip_y = target_pos.y() + grip_offset_y
                curr_hx = grip_x + 600.0 * eased_retreat
                curr_hy = grip_y + 500.0 * eased_retreat
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": True,
                    "hand_pos": QPointF(curr_hx, curr_hy),
                    "hand_scale": 1.0,
                    "sfx_hint": None
                }
            else:
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": None
                }

        # ---------------------------------------------------------
        # STYLE 2: Hand Push & Slide
        # ---------------------------------------------------------
        elif "hand_push" in motion_style or "push" in motion_style:
            start_pos = cls.compute_entry_start_pos(direction, artboard_rect, item_rect, target_pos, item_scale)
            push_dur = motion_duration * 0.82
            settle_dur = motion_duration * 0.06
            lift_dur = motion_duration * 0.12

            dir_clean = (direction or "left").lower().replace("-", "_")
            if "right" in dir_clean:
                # Pushing from the right trailing edge moving left
                push_offset_x = w + 15.0
                push_offset_y = h * 0.40
            elif "top" in dir_clean and "left" not in dir_clean and "right" not in dir_clean:
                # Pushing from top trailing edge moving down
                push_offset_x = w * 0.50
                push_offset_y = -25.0
            elif "bottom" in dir_clean and "left" not in dir_clean and "right" not in dir_clean:
                # Pushing from bottom trailing edge moving up
                push_offset_x = w * 0.50
                push_offset_y = h + 25.0
            else:
                # Pushing from left trailing edge moving right
                push_offset_x = -35.0
                push_offset_y = h * 0.40

            if time_in_item <= push_dur:
                progress = time_in_item / push_dur if push_dur > 0 else 1.0
                eased = easing_fn(progress)
                curr_x = start_pos.x() + (target_pos.x() - start_pos.x()) * eased
                curr_y = start_pos.y() + (target_pos.y() - start_pos.y()) * eased
                curr_pos = QPointF(curr_x, curr_y)
                hand_pos = QPointF(curr_x + push_offset_x, curr_y + push_offset_y)
                return {
                    "item_pos": curr_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": True,
                    "hand_pos": hand_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": "whoosh" if progress < 0.2 else None
                }
            elif time_in_item <= push_dur + settle_dur:
                hand_pos = QPointF(target_pos.x() + push_offset_x, target_pos.y() + push_offset_y)
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": True,
                    "hand_pos": hand_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": "impact"
                }
            elif time_in_item <= motion_duration:
                lift_t = (time_in_item - (push_dur + settle_dur)) / lift_dur if lift_dur > 0 else 1.0
                eased_lift = lift_t * lift_t
                hx = target_pos.x() + push_offset_x + 500.0 * eased_lift
                hy = target_pos.y() + push_offset_y + 400.0 * eased_lift
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": True,
                    "hand_pos": QPointF(hx, hy),
                    "hand_scale": 1.0,
                    "sfx_hint": None
                }
            else:
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": None
                }

        # ---------------------------------------------------------
        # STYLE 3: Gravity Drop & Bounce (Physical fall from ceiling)
        # ---------------------------------------------------------
        elif "gravity" in motion_style or "drop" in motion_style:
            drop_start_y = artboard_rect.top() - h - 180.0
            total_drop = target_pos.y() - drop_start_y
            fall_dur = motion_duration * 0.52
            bounce1_dur = motion_duration * 0.28
            bounce2_dur = motion_duration * 0.20

            if time_in_item <= fall_dur:
                t = time_in_item / fall_dur if fall_dur > 0 else 1.0
                # Gravitational acceleration t^2
                eased = t * t
                curr_y = drop_start_y + total_drop * eased
                return {
                    "item_pos": QPointF(target_pos.x(), curr_y),
                    "item_scale_mult": 1.0,
                    "item_opacity": min(1.0, t * 2.5),
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": "whoosh" if t < 0.25 else None
                }
            elif time_in_item <= fall_dur + bounce1_dur:
                bt = (time_in_item - fall_dur) / bounce1_dur if bounce1_dur > 0 else 1.0
                # Parabolic rebound curve: 4 * t * (1 - t)
                h1 = max(40.0, total_drop * 0.16)
                offset_y = -h1 * 4.0 * bt * (1.0 - bt)
                # Subtle squash at ground impact
                squash = 0.94 if bt < 0.15 or bt > 0.85 else 1.02
                return {
                    "item_pos": QPointF(target_pos.x(), target_pos.y() + offset_y),
                    "item_scale_mult": squash,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": "impact" if bt < 0.1 else None
                }
            elif time_in_item <= motion_duration:
                bt2 = (time_in_item - (fall_dur + bounce1_dur)) / bounce2_dur if bounce2_dur > 0 else 1.0
                h2 = max(12.0, total_drop * 0.04)
                offset_y = -h2 * 4.0 * bt2 * (1.0 - bt2)
                return {
                    "item_pos": QPointF(target_pos.x(), target_pos.y() + offset_y),
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": None
                }
            else:
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": None
                }

        # ---------------------------------------------------------
        # STYLE 4: 3D Flip Card Reveal
        # ---------------------------------------------------------
        elif "flip" in motion_style or "3d" in motion_style:
            flip_dur = motion_duration * 0.78
            if time_in_item <= flip_dur:
                progress = time_in_item / flip_dur if flip_dur > 0 else 1.0
                eased = cls.ease_smooth(progress)
                angle = (1.0 - eased) * 90.0
                rad = math.radians(angle)
                # Projected scale along horizontal dimension
                proj_scale = max(0.01, math.cos(rad))
                curr_x = target_pos.x() + (w * (1.0 - proj_scale) * 0.5)
                opacity = min(1.0, max(0.0, progress * 2.2))
                return {
                    "item_pos": QPointF(curr_x, target_pos.y()),
                    "item_scale_mult": proj_scale,
                    "item_opacity": opacity,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": "whoosh" if progress < 0.2 else None
                }
            else:
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": "impact" if time_in_item <= flip_dur + 0.05 else None
                }

        # ---------------------------------------------------------
        # STYLE 5: Cinematic Zoom & Focus
        # ---------------------------------------------------------
        elif "zoom" in motion_style or "cinematic" in motion_style:
            zoom_dur = motion_duration * 0.78
            dir_clean = (direction or "").lower()
            start_scale = 2.4 if ("out" in dir_clean or "top" in dir_clean) else 0.18
            if time_in_item <= zoom_dur:
                progress = time_in_item / zoom_dur if zoom_dur > 0 else 1.0
                eased = cls.ease_back(progress) if start_scale < 1.0 else cls.ease_smooth(progress)
                scale_mult = start_scale + (1.0 - start_scale) * eased
                scale_mult = max(0.01, scale_mult)
                # Keep center pinned so it zooms outward from its natural midpoint
                curr_x = target_pos.x() + (w * (1.0 - scale_mult) * 0.5)
                curr_y = target_pos.y() + (h * (1.0 - scale_mult) * 0.5)
                opacity = min(1.0, max(0.0, progress * 2.0))
                return {
                    "item_pos": QPointF(curr_x, curr_y),
                    "item_scale_mult": scale_mult,
                    "item_opacity": opacity,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": "whoosh" if progress < 0.2 else None
                }
            else:
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": None
                }

        # ---------------------------------------------------------
        # STYLE 6: Arc / Orbital Glide (Curved trajectory)
        # ---------------------------------------------------------
        elif "arc" in motion_style or "orbital" in motion_style:
            start_pos = cls.compute_entry_start_pos(direction, artboard_rect, item_rect, target_pos, item_scale)
            arc_dur = motion_duration * 0.80
            # Calculate Bezier quadratic control point perpendicular to trajectory
            mid_x = (start_pos.x() + target_pos.x()) * 0.5
            mid_y = (start_pos.y() + target_pos.y()) * 0.5
            dx = target_pos.x() - start_pos.x()
            dy = target_pos.y() - start_pos.y()
            length = math.hypot(dx, dy)
            if length > 0.001:
                perp_x = -dy / length
                perp_y = dx / length
            else:
                perp_x, perp_y = 0.0, 1.0
            curve_magnitude = min(220.0, max(80.0, length * 0.25))
            ctrl_x = mid_x + perp_x * curve_magnitude
            ctrl_y = mid_y + perp_y * curve_magnitude

            if time_in_item <= arc_dur:
                progress = time_in_item / arc_dur if arc_dur > 0 else 1.0
                eased = easing_fn(progress)
                # Quadratic Bezier formula: (1-t)^2 * P0 + 2*(1-t)*t * P1 + t^2 * P2
                omt = 1.0 - eased
                bx = omt * omt * start_pos.x() + 2.0 * omt * eased * ctrl_x + eased * eased * target_pos.x()
                by = omt * omt * start_pos.y() + 2.0 * omt * eased * ctrl_y + eased * eased * target_pos.y()
                opacity = min(1.0, max(0.0, progress * 2.0))
                return {
                    "item_pos": QPointF(bx, by),
                    "item_scale_mult": 1.0,
                    "item_opacity": opacity,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": "whoosh" if progress < 0.2 else None
                }
            else:
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": None
                }

        # ---------------------------------------------------------
        # STYLE 7: Directional Slide-In (Linear / 8-way, no hand)
        # ---------------------------------------------------------
        elif "slide" in motion_style:
            start_pos = cls.compute_entry_start_pos(direction, artboard_rect, item_rect, target_pos, item_scale)
            slide_dur = motion_duration * 0.78
            if time_in_item <= slide_dur:
                progress = time_in_item / slide_dur if slide_dur > 0 else 1.0
                eased = easing_fn(progress)
                curr_x = start_pos.x() + (target_pos.x() - start_pos.x()) * eased
                curr_y = start_pos.y() + (target_pos.y() - start_pos.y()) * eased
                opacity = min(1.0, max(0.0, progress * 1.6))
                return {
                    "item_pos": QPointF(curr_x, curr_y),
                    "item_scale_mult": 1.0,
                    "item_opacity": opacity,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": "whoosh" if progress < 0.2 else None
                }
            else:
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": None
                }

        # ---------------------------------------------------------
        # STYLE 8: Elastic Pop & Scale (Spring bounce from center)
        # ---------------------------------------------------------
        else: # elastic_pop
            pop_dur = motion_duration * 0.78
            if time_in_item <= pop_dur:
                progress = time_in_item / pop_dur if pop_dur > 0 else 1.0
                eased = cls.ease_elastic(progress)
                opacity = min(1.0, max(0.0, progress * 2.2))
                scale_mult = max(0.001, eased)
                curr_x = target_pos.x() + (w * (1.0 - scale_mult) * 0.5)
                curr_y = target_pos.y() + (h * (1.0 - scale_mult) * 0.5)
                return {
                    "item_pos": QPointF(curr_x, curr_y),
                    "item_scale_mult": scale_mult,
                    "item_opacity": opacity,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": "whoosh" if progress < 0.15 else None
                }
            else:
                return {
                    "item_pos": target_pos,
                    "item_scale_mult": 1.0,
                    "item_opacity": 1.0,
                    "item_rotation_offset": 0.0,
                    "hand_visible": False,
                    "hand_pos": target_pos,
                    "hand_scale": 1.0,
                    "sfx_hint": None
                }
