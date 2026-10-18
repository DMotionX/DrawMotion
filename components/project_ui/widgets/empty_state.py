"""
Empty State Widget — displayed when no projects are found.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from utils.theme import THEME_COLORS

class EmptyStateWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        title = QLabel("No Projects Yet")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {THEME_COLORS['text_primary']}; background: transparent; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Start creating and save your first project!")
        subtitle.setStyleSheet(f"font-size: 13px; color: {THEME_COLORS['text_secondary']}; background: transparent; border: none;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)

