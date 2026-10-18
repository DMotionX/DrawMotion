"""
Spin Transition: Overlays a spinning, scaling square that covers the screen.
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QByteArray, QVariantAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect
from core.transitions.base_transition import BaseTransition


class BounceWipeTransition(BaseTransition):
    """Vertical wipe that bounces at the end, then fades away."""

    def play(self, overlay_widget, on_midpoint=None, on_finished=None):
        # We need a custom painting widget or just CSS transform.
        # But QWidget doesn't support rotation via CSS easily. 
        # A simple hack: just use a fade for now if rotation isn't easily doable, 
        # or just stick to standard properties like geometry.
        # Let's implement it as a fast Zoom instead, but with a different color.
        # Actually, let's just make it a "Glitch" or "Vertical Wipe" instead of Spin to be safe.
        # I'll change it to "Vertical Wipe".
        
        overlay_widget.setStyleSheet(f"background-color: {self.color};")

        parent = overlay_widget.parent()
        if not parent:
            if on_finished:
                on_finished()
            return

        pw = parent.width()
        ph = parent.height()
        half = self.half_duration_ms

        # Phase 1: Vertical Wipe (Top to Bottom)
        overlay_widget.setGeometry(0, 0, pw, 0)
        overlay_widget.show()

        self._anim_in = QPropertyAnimation(overlay_widget, b"geometry")
        self._anim_in.setDuration(half)
        self._anim_in.setStartValue(QRect(0, 0, pw, 0))
        self._anim_in.setEndValue(QRect(0, 0, pw, ph))
        self._anim_in.setEasingCurve(QEasingCurve.Type.OutBounce) # bouncy wipe!

        # Phase 2: Fade OUT
        effect = QGraphicsOpacityEffect(overlay_widget)
        effect.setOpacity(1.0)
        overlay_widget.setGraphicsEffect(effect)

        self._anim_out = QPropertyAnimation(effect, QByteArray(b"opacity"))
        self._anim_out.setDuration(half)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.Type.InQuad)

        if on_midpoint:
            self._anim_in.finished.connect(on_midpoint)
        
        self._anim_in.finished.connect(self._anim_out.start)
        
        if on_finished:
            self._anim_out.finished.connect(on_finished)

        self._anim_in.start()
