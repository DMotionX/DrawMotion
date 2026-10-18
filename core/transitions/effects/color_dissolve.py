"""
Color Dissolve Transition: Fades into a rich color, then to black, then fades out.
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QByteArray, QSequentialAnimationGroup
from PySide6.QtWidgets import QGraphicsOpacityEffect
from core.transitions.base_transition import BaseTransition


class ColorDissolveTransition(BaseTransition):
    """Cinematic color dissolve."""

    def play(self, overlay_widget, on_midpoint=None, on_finished=None):
        # We will use opacity to fade in the color
        overlay_widget.setStyleSheet(f"background-color: {self.color};")

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

        # Fade IN
        self._anim_in = QPropertyAnimation(effect, QByteArray(b"opacity"))
        self._anim_in.setDuration(half)
        self._anim_in.setStartValue(0.0)
        self._anim_in.setEndValue(1.0)
        self._anim_in.setEasingCurve(QEasingCurve.Type.InOutSine)

        # Fade OUT
        self._anim_out = QPropertyAnimation(effect, QByteArray(b"opacity"))
        self._anim_out.setDuration(half)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.Type.InOutSine)

        if on_midpoint:
            self._anim_in.finished.connect(on_midpoint)
        
        self._anim_in.finished.connect(self._anim_out.start)
        
        if on_finished:
            self._anim_out.finished.connect(on_finished)

        self._anim_in.start()
