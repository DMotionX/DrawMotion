"""
Base for all four timeline layer rows.
Each layer exposes TWO widgets:
  - label_widget():  shown in the LEFT "LAYERS" column
  - track_widget():  shown in the RIGHT timeline area

This separation guarantees:
  1. Label column width is controlled by the panel, not the row.
  2. Track width stretches freely with the timeline.
  3. Heights are always in sync because both widgets have the same TRACK_HEIGHT.
"""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor
from utils.theme import THEME_COLORS

TRACK_HEIGHT = 36     # px — every row has this exact height
TRACK_SPACING = 4     # px — vertical gap between rows


class _IconWidget(QWidget):
    """Tiny widget that delegates its paintEvent to a custom draw function."""
    def __init__(self, draw_func, parent=None):
        super().__init__(parent)
        self._draw_func = draw_func
        self.setFixedSize(18, 18)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_func(painter, self.rect())
        painter.end()


class BaseLayerRow:
    """
    Abstract base — NOT a QWidget itself.
    Provides two QFrame widgets that the panel places in its two columns.
    """
    LABEL_TEXT  = "Layer"
    ACCENT_COLOR = "#2E8B57"

    def __init__(self, workspace=None, pixels_per_second: int = 50):
        self._workspace = workspace
        self._pps = pixels_per_second
        self._label_frame = self._build_label_frame()
        self._track_frame = self._build_track_frame()
        self._populate_track()

    # ── Public accessors ────────────────────────────────────────────
    def label_widget(self) -> QFrame:
        return self._label_frame

    def track_widget(self) -> QFrame:
        return self._track_frame

    def refresh(self):
        self._populate_track()

    # ── Internal builders ───────────────────────────────────────────
    def _build_label_frame(self) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(TRACK_HEIGHT)
        frame.setStyleSheet(
            f"background-color: {THEME_COLORS['bg_main']};"
            f"border-right: 2px solid {self.ACCENT_COLOR};"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(7)

        icon_w = _IconWidget(self.draw_icon)
        layout.addWidget(icon_w)

        lbl = QLabel(self.LABEL_TEXT)
        lbl.setStyleSheet(
            f"color: {THEME_COLORS['text_primary']};"
            f"font-size: 11px; font-weight: 600; background: transparent; border: none;"
        )
        layout.addWidget(lbl)
        layout.addStretch()
        return frame

    def _build_track_frame(self) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(TRACK_HEIGHT)
        frame.setStyleSheet(f"background-color: {THEME_COLORS['bg_secondary']}; border: none;")

        self._track_layout = QHBoxLayout(frame)
        self._track_layout.setContentsMargins(0, 3, 0, 3)
        self._track_layout.setSpacing(0)
        self._track_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        return frame

    def _clear_track(self):
        while self._track_layout.count():
            child = self._track_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

    # ── Subclass interface ──────────────────────────────────────────
    def draw_icon(self, painter: QPainter, rect):
        """Override to paint the layer icon."""
        pass

    def _populate_track(self):
        """Override to add DraggableBlock / TransitionBlock widgets to self._track_layout."""
        self._clear_track()
        self._track_layout.addStretch()
