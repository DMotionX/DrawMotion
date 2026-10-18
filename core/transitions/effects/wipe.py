"""
Wipe Transition: A color wipes across the screen from left to right, then wipes back.
"""
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect
from core.transitions.base_transition import BaseTransition


class WipeTransition(BaseTransition):
    """A solid bar grows from the left edge until it covers the screen, then shrinks away."""

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

        overlay_widget.setGeometry(QRect(0, 0, 0, ph))
        overlay_widget.show()

        # Phase 1: Wipe IN (width grows 0 → full)
        self._anim_in = QPropertyAnimation(overlay_widget, b"geometry")
        self._anim_in.setDuration(half)
        self._anim_in.setStartValue(QRect(0, 0, 0, ph))
        self._anim_in.setEndValue(QRect(0, 0, pw, ph))
        self._anim_in.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Phase 2: Wipe OUT (left edge moves right, shrinking)
        self._anim_out = QPropertyAnimation(overlay_widget, b"geometry")
        self._anim_out.setDuration(half)
        self._anim_out.setStartValue(QRect(0, 0, pw, ph))
        self._anim_out.setEndValue(QRect(pw, 0, 0, ph))
        self._anim_out.setEasingCurve(QEasingCurve.Type.InOutCubic)

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
