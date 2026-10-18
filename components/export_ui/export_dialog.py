"""
Export Dialog — redesigned with a professional card-based layout,
ETA timer, English-only progress display, and full-width design.
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog,
    QWidget, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from .widgets.settings_panel import ExportSettingsPanel
from .widgets.progress_panel import ExportProgressPanel
from core.export_engine.export_service import ExportService
from utils.theme import THEME_COLORS


DIALOG_STYLE = """
    QDialog {
        background-color: #0E1512;
        color: #D0D8D4;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QFrame#header_card {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 #1A3028, stop:1 #111D18
        );
        border-bottom: 1px solid #253530;
        border-radius: 0px;
    }
    QFrame#settings_card {
        background-color: #131C18;
        border: 1px solid #1E2E28;
        border-radius: 10px;
    }
    QLabel#dialog_title {
        font-size: 20px;
        font-weight: 700;
        color: #D0D8D4;
    }
    QLabel#dialog_subtitle {
        font-size: 12px;
        color: #5A7A6A;
    }
    QLabel#section_label {
        font-size: 11px;
        font-weight: 600;
        color: #4A8060;
        letter-spacing: 1px;
    }
"""


class ExportDialog(QDialog):
    """
    Professional Export Dialog with:
    - Card-based settings layout
    - ETA timer during export
    - English-only progress percentage
    - Default save path from settings
    """

    def __init__(self, scene, engine, user_items, audio_items, parent=None):
        super().__init__(parent)
        self.export_service = ExportService(scene, engine, user_items, audio_items, self)

        # Connect backend signals
        self.export_service.progress_updated.connect(self._on_progress_updated)
        self.export_service.export_finished.connect(self._on_export_finished)
        self.export_service.export_error.connect(self._on_export_error)

        # ETA timer
        self._export_start_time = None
        self._eta_timer = QTimer(self)
        self._eta_timer.timeout.connect(self._update_eta)

        self.setWindowTitle("Export Video")
        self.setMinimumSize(560, 440)
        self.setMaximumWidth(640)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(DIALOG_STYLE)
        self._init_ui()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("header_card")
        header.setFixedHeight(80)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(28, 0, 28, 0)

        icon_lbl = QFrame()
        icon_lbl.setFixedSize(44, 44)
        icon_lbl.setStyleSheet("""
            QFrame {
                background-color: #2D6A4F;
                border-radius: 10px;
                border: none;
            }
        """)
        icon_inner = QVBoxLayout(icon_lbl)
        icon_inner.setContentsMargins(0, 0, 0, 0)
        icon_text = QLabel("EX")
        icon_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_text.setStyleSheet("color: white; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        icon_inner.addWidget(icon_text)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title = QLabel("Export Video")
        title.setObjectName("dialog_title")

        subtitle = QLabel("Configure your export settings and save the final video.")
        subtitle.setObjectName("dialog_subtitle")

        text_col.addWidget(title)
        text_col.addWidget(subtitle)

        h_layout.addWidget(icon_lbl)
        h_layout.addSpacing(14)
        h_layout.addLayout(text_col)
        h_layout.addStretch()

        root.addWidget(header)

        # ── Body ──────────────────────────────────────────────────────────────
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 24)
        body_layout.setSpacing(16)

        # Settings section label
        settings_lbl = QLabel("EXPORT SETTINGS")
        settings_lbl.setObjectName("section_label")
        body_layout.addWidget(settings_lbl)

        # Settings card
        settings_card = QFrame()
        settings_card.setObjectName("settings_card")
        card_layout = QVBoxLayout(settings_card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(4)

        self.settings_panel = ExportSettingsPanel(self)
        card_layout.addWidget(self.settings_panel)
        body_layout.addWidget(settings_card)

        # ETA label
        self.eta_label = QLabel("")
        self.eta_label.setStyleSheet(
            "color: #4A8060; font-size: 12px; background: transparent;"
        )
        self.eta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.eta_label.hide()
        body_layout.addWidget(self.eta_label)

        body_layout.addStretch()

        # Progress + buttons
        progress_lbl = QLabel("EXPORT PROGRESS")
        progress_lbl.setObjectName("section_label")
        body_layout.addWidget(progress_lbl)

        self.progress_panel = ExportProgressPanel(self)
        self.progress_panel.cancel_requested.connect(self._on_cancel)
        self.progress_panel.start_requested.connect(self._start_export)
        body_layout.addWidget(self.progress_panel)

        root.addWidget(body, 1)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_cancel(self):
        self._eta_timer.stop()
        self.export_service.cancel()
        self.reject()

    def _start_export(self):
        from core.settings_manager import SettingsManager
        import os
        from datetime import datetime
        
        settings = SettingsManager()
        default_dir = settings.get("default_export_path", "")
        if not default_dir:
            default_dir = os.path.join(os.path.expanduser("~"), "Documents", "DrawMotion", "Exports")
            
        os.makedirs(default_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"DrawMotion_Export_{timestamp}.mp4"
        file_path = os.path.join(default_dir, file_name)
            
        # FIX: Clear selection so blue borders don't show in the video
        if hasattr(self.export_service, 'scene') and self.export_service.scene:
            self.export_service.scene.clearSelection()

        resolution_label = self.settings_panel.get_resolution()
        fps = self.settings_panel.get_fps()
        fmt = self.settings_panel.get_format()

        # Persist choices
        settings.set("export_resolution", resolution_label.split(" ")[0])
        settings.set("export_fps", fps)
        settings.set("export_format", fmt)

        self.settings_panel.set_enabled(False)
        self.progress_panel.prepare_for_export()

        # Start ETA tracking
        import time
        self._export_start_time = time.time()
        self._last_progress = 0
        self.eta_label.setText(f"Exporting to: {default_dir}")
        self.eta_label.show()
        self._eta_timer.start(1000)

        self.export_service.start_export(
            file_path, resolution_label=resolution_label, fps=fps
        )

    def _on_progress_updated(self, progress: int):
        self._last_progress = progress
        self.progress_panel.update_progress(progress)

    def _update_eta(self):
        import time
        if self._export_start_time is None:
            return
        elapsed = time.time() - self._export_start_time
        prog = getattr(self, '_last_progress', 0)
        if prog > 2:
            remaining = (elapsed / prog) * (100 - prog)
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            if mins > 0:
                self.eta_label.setText(f"Estimated time remaining: {mins}m {secs:02d}s")
            else:
                self.eta_label.setText(f"Estimated time remaining: {secs}s")

    def _on_export_finished(self, path: str):
        self._eta_timer.stop()
        self.eta_label.setText("Export complete")
        self.progress_panel.set_finished(path)
        
        # Optionally, open the folder
        import subprocess, sys, os
        try:
            folder = os.path.dirname(path)
            if sys.platform == 'win32':
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])
        except Exception as e:
            print(f"Failed to open folder: {e}")

    def _on_export_error(self, error: str):
        self._eta_timer.stop()
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            self, "Export Failed",
            f"An error occurred during export:\n{error}"
        )
        self.reject()
