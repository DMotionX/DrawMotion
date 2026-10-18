"""
Flash Transition: Flashes a bright white screen and then fades out.
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QByteArray
from PySide6.QtWidgets import QGraphicsOpacityEffect
from core.transitions.base_transition import BaseTransition


class FlashTransition(BaseTransition):
    """Flashes a white overlay and then fades out."""

    def play(self, overlay_widget, on_midpoint=None, on_finished=None):
        overlay_widget.setStyleSheet("background-color: #FFFFFF;")

        parent = overlay_widget.parent()
        if not parent:
            if on_finished:
                on_finished()
            return

        overlay_widget.setGeometry(0, 0, parent.width(), parent.height())
        overlay_widget.show()

        effect = QGraphicsOpacityEffect(overlay_widget)
        effect.setOpacity(0.0)
        overlay_widget.setGraphicsEffect(effect)

        half = self.half_duration_ms

        # Fade IN quickly to white
        self._anim_in = QPropertyAnimation(effect, QByteArray(b"opacity"))
        self._anim_in.setDuration(half)
        self._anim_in.setStartValue(0.0)
        self._anim_in.setEndValue(1.0)
        self._anim_in.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Fade OUT
        self._anim_out = QPropertyAnimation(effect, QByteArray(b"opacity"))
        self._anim_out.setDuration(half)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.Type.InQuad)

        # Connect signals
        if on_midpoint:
            self._anim_in.finished.connect(on_midpoint)
        
        self._anim_in.finished.connect(self._anim_out.start)
        
        if on_finished:
            self._anim_out.finished.connect(on_finished)

        self._anim_in.start()
