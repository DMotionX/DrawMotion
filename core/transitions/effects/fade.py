"""
Fade Transition: Fades the screen to the chosen color, then fades back.
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QByteArray
from PySide6.QtWidgets import QGraphicsOpacityEffect
from core.transitions.base_transition import BaseTransition


class FadeTransition(BaseTransition):
    """Screen fades to a solid color then fades back to reveal the next scene."""

    def play(self, overlay_widget, on_midpoint=None, on_finished=None):
        # We don't need background-color because overlay_widget is now a QLabel containing a snapshot
        overlay_widget.setWindowOpacity(1.0)

        # Apply opacity effect to the overlay
        effect = QGraphicsOpacityEffect(overlay_widget)
        effect.setOpacity(1.0)
        overlay_widget.setGraphicsEffect(effect)
        overlay_widget.show()

        # Fade OUT the snapshot (opaque → transparent)
        self._anim_out = QPropertyAnimation(effect, QByteArray(b"opacity"))
        self._anim_out.setDuration(self.duration_ms)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def _on_out_finished():
            if on_finished:
                on_finished()

        self._anim_out.finished.connect(_on_out_finished)
        self._anim_out.start()
