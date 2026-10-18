"""
Export Progress Panel — Progress bar with English-only % display,
animated pulse effect, and transforming Start/Open Folder button.
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QLabel
)
from PySide6.QtCore import Signal, Qt, QLocale
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from utils.theme import THEME_COLORS

BTN_STYLE_CANCEL = """
    QPushButton {
        background: transparent;
        color: #5A7A6A;
        border: 1px solid #253530;
        padding: 10px 24px;
        border-radius: 7px;
        font-size: 13px;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #1A2520;
        color: #D0D8D4;
        border-color: #2E5040;
    }
"""

BTN_STYLE_START = """
    QPushButton {
        background-color: #2E8B57;
        color: white;
        border: none;
        padding: 10px 32px;
        border-radius: 7px;
        font-size: 14px;
        font-weight: 700;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QPushButton:hover  { background-color: #38A169; }
    QPushButton:pressed { background-color: #276749; }
    QPushButton:disabled {
        background-color: #1E3028;
        color: #3A5040;
    }
"""

BTN_STYLE_DONE = """
    QPushButton {
        background-color: #1E5C3A;
        color: #5EE09A;
        border: 1px solid #2E8B57;
        padding: 10px 32px;
        border-radius: 7px;
        font-size: 14px;
        font-weight: 700;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QPushButton:hover { background-color: #2E8B57; color: white; }
"""

PROGRESS_STYLE = """
    QProgressBar {
        border: none;
        border-radius: 6px;
        background-color: #1A2520;
        text-align: center;
        color: white;
        font-size: 12px;
        font-weight: 600;
        font-family: 'Segoe UI', Arial, sans-serif;
        min-height: 24px;
    }
    QProgressBar::chunk {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 #2E8B57, stop:1 #3CB371
        );
        border-radius: 6px;
    }
"""


class ExportProgressPanel(QWidget):
    """
    Progress + action button panel.
    - Progress % shown in English only (QLocale fix)
    - Button transforms from Start → Open Folder on completion
    """
    cancel_requested = Signal()
    start_requested  = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_path = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Progress Bar (hidden until export starts)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(PROGRESS_STYLE)
        self.progress_bar.setLocale(QLocale(QLocale.Language.English))  # Fix Arabic numerals
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(BTN_STYLE_CANCEL)
        self.cancel_btn.setFixedHeight(44)
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)

        self.action_btn = QPushButton("Start Export")
        self.action_btn.setStyleSheet(BTN_STYLE_START)
        self.action_btn.setFixedHeight(44)
        self.action_btn.clicked.connect(self._on_action_clicked)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.action_btn, 1)  # Action button takes remaining width
        layout.addLayout(btn_row)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_action_clicked(self):
        if self.action_btn.text().endswith("Start Export"):
            self.start_requested.emit()
        elif self.action_btn.text().endswith("Open Folder"):
            if self.output_path:
                folder = os.path.dirname(self.output_path)
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def prepare_for_export(self):
        self.action_btn.setEnabled(False)
        self.action_btn.setText("Exporting…")
        self.progress_bar.setValue(0)
        self.progress_bar.show()

    def update_progress(self, progress: int):
        self.progress_bar.setValue(progress)

    def set_finished(self, output_path: str):
        self.output_path = output_path
        self.action_btn.setText("Open Folder")
        self.action_btn.setStyleSheet(BTN_STYLE_DONE)

        self.action_btn.setEnabled(True)
        self.progress_bar.setValue(100)
