"""
Iris Transition: A circular mask closes in from the edges to cover the screen,
then opens back from the center — like a camera iris/aperture effect.
Implemented by animating the size of a circular overlay using paintEvent.
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property, QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPainterPath
from core.transitions.base_transition import BaseTransition


class IrisOverlay(QWidget):
    """Custom widget that draws a circular iris mask over the canvas."""

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._radius = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)

    def _get_radius(self):
        return self._radius

    def _set_radius(self, value: float):
        self._radius = value
        self.update()

    radius = Property(float, _get_radius, _set_radius)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Max radius needed to cover screen corners
        max_radius = ((w ** 2 + h ** 2) ** 0.5) / 2

        # Fill the whole widget with the color
        painter.fillRect(self.rect(), self._color)

        # Cut a transparent circle in the center
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        path = QPainterPath()
        path.addEllipse(w / 2 - self._radius, h / 2 - self._radius,
                        self._radius * 2, self._radius * 2)
        painter.fillPath(path, QColor(0, 0, 0, 0))


class IrisTransition(BaseTransition):
    """Circular iris closes over the screen then opens to reveal the next scene."""

    def play(self, overlay_widget, on_midpoint=None, on_finished=None):
        parent = overlay_widget.parent()
        if not parent:
            if on_finished:
                on_finished()
            return

        pw = parent.width()
        ph = parent.height()
        max_r = ((pw ** 2 + ph ** 2) ** 0.5) / 2
        half = self.half_duration_ms

        # Replace the generic overlay with our custom IrisOverlay
        iris = IrisOverlay(self.color, parent)
        iris.setGeometry(0, 0, pw, ph)
        iris._set_radius(max_r)   # Start open
        iris.show()

        # Phase 1: Close iris (radius → 0)
        self._anim_in = QPropertyAnimation(iris, b"radius")
        self._anim_in.setDuration(half)
        self._anim_in.setStartValue(max_r)
        self._anim_in.setEndValue(0.0)
        self._anim_in.setEasingCurve(QEasingCurve.Type.InOutQuart)

        # Phase 2: Open iris (radius → max)
        self._anim_out = QPropertyAnimation(iris, b"radius")
        self._anim_out.setDuration(half)
        self._anim_out.setStartValue(0.0)
        self._anim_out.setEndValue(max_r)
        self._anim_out.setEasingCurve(QEasingCurve.Type.InOutQuart)

        def _on_in_finished():
            if on_midpoint:
                on_midpoint()
            self._anim_out.start()

        def _on_out_finished():
            iris.hide()
            iris.deleteLater()
            if on_finished:
                on_finished()

        self._anim_in.finished.connect(_on_in_finished)
        self._anim_out.finished.connect(_on_out_finished)
        self._anim_in.start()
