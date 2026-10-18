"""
Split Transition: Expands from the center horizontally to cover the screen.
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QByteArray
from PySide6.QtWidgets import QGraphicsOpacityEffect
from core.transitions.base_transition import BaseTransition


class SplitTransition(BaseTransition):
    """Expands horizontally from the center to cover the screen, then fades out."""

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

        center_x = pw // 2

        # Phase 1: Expand horizontally from center
        overlay_widget.setGeometry(QRect(center_x, 0, 0, ph))
        overlay_widget.show()

        self._anim_in = QPropertyAnimation(overlay_widget, b"geometry")
        self._anim_in.setDuration(half)
        self._anim_in.setStartValue(QRect(center_x, 0, 0, ph))
        self._anim_in.setEndValue(QRect(0, 0, pw, ph))
        self._anim_in.setEasingCurve(QEasingCurve.Type.OutQuart)

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
