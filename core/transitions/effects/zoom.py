"""
Zoom Transition: The overlay scales from small to full size then fades out.
Gives a zoom-punch feel between scenes.
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QByteArray
from PySide6.QtWidgets import QGraphicsOpacityEffect
from core.transitions.base_transition import BaseTransition


class ZoomTransition(BaseTransition):
    """Overlay zooms from center outward to cover screen, then fades away."""

    def play(self, overlay_widget, on_midpoint=None, on_finished=None):
        overlay_widget.setStyleSheet(f"background-color: {self.color};")

        parent = overlay_widget.parent()
        if not parent:
            if on_finished:
                on_finished()
            return

        pw = parent.width()
        ph = parent.height()
        half = self.half_duration_ms

        # Start as a tiny box in the center
        center_x = pw // 2
        center_y = ph // 2

        overlay_widget.setGeometry(QRect(center_x, center_y, 0, 0))
        overlay_widget.show()

        # Phase 1: Zoom IN — tiny to full screen
        self._anim_in = QPropertyAnimation(overlay_widget, b"geometry")
        self._anim_in.setDuration(half)
        self._anim_in.setStartValue(QRect(center_x, center_y, 0, 0))
        self._anim_in.setEndValue(QRect(0, 0, pw, ph))
        self._anim_in.setEasingCurve(QEasingCurve.Type.OutExpo)

        # Phase 2: Fade OUT — full screen fades to transparent
        effect = QGraphicsOpacityEffect(overlay_widget)
        effect.setOpacity(1.0)
        overlay_widget.setGraphicsEffect(effect)

        self._anim_out = QPropertyAnimation(effect, QByteArray(b"opacity"))
        self._anim_out.setDuration(half)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.Type.InQuad)

        def _on_in_finished():
            if on_midpoint:
                on_midpoint()
            self._anim_out.start()

        def _on_out_finished():
            if on_finished:
                on_finished()

        self._anim_in.finished.connect(_on_in_finished)
        self._anim_out.finished.connect(_on_out_finished)
        self._anim_in.start()
