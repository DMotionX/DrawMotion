"""
Slide Transition: A colored panel slides in from the right, then slides out to the left.
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect
from core.transitions.base_transition import BaseTransition


class SlideTransition(BaseTransition):
    """A solid colored bar slides in from the right edge then exits to the left."""

    def play(self, overlay_widget, on_midpoint=None, on_finished=None):
        parent = overlay_widget.parent()
        if not parent:
            if on_finished:
                on_finished()
            return

        pw = parent.width()
        ph = parent.height()

        # Snapshot starts exactly where it was taken
        overlay_widget.setGeometry(QRect(0, 0, pw, ph))
        overlay_widget.show()

        # Slide OUT (center → left) to reveal the new scene
        self._anim_out = QPropertyAnimation(overlay_widget, b"geometry")
        self._anim_out.setDuration(self.duration_ms)
        self._anim_out.setStartValue(QRect(0, 0, pw, ph))
        self._anim_out.setEndValue(QRect(-pw, 0, pw, ph))
        self._anim_out.setEasingCurve(QEasingCurve.Type.InOutQuart)

        def _on_out_finished():
            if on_finished:
                on_finished()

        self._anim_out.finished.connect(_on_out_finished)
        self._anim_out.start()
