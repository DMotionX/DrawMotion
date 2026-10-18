"""
Export Settings Panel — redesigned with icon badges per option
and full-width combo boxes for a professional look.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
)
from PySide6.QtCore import Qt, QLocale
from core.settings_manager import SettingsManager

COMBO_STYLE = """
    QComboBox {
        background-color: #0E1512;
        color: #D0D8D4;
        border: 1px solid #253530;
        border-radius: 7px;
        padding: 9px 14px;
        font-size: 13px;
        font-family: 'Segoe UI', Arial, sans-serif;
        min-height: 38px;
    }
    QComboBox:hover {
        border: 1px solid #2E8B57;
        background-color: #111D18;
    }
    QComboBox:focus {
        border: 2px solid #2E8B57;
    }
    QComboBox::drop-down {
        border: none;
        width: 28px;
    }
    QComboBox QAbstractItemView {
        background-color: #131C18;
        color: #D0D8D4;
        border: 1px solid #253530;
        selection-background-color: #2E8B57;
        selection-color: white;
        outline: 0;
    }
"""

LABEL_STYLE = "color: #7A9E90; font-size: 12px; min-width: 130px; font-family: 'Segoe UI', Arial;"
ICON_STYLE  = "font-size: 16px; background: transparent; border: none; min-width: 24px;"


class ExportSettingsPanel(QWidget):
    """
    Settings panel showing Resolution, FPS, and Format selectors.
    Loads defaults from SettingsManager and uses English locale for all values.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        settings = SettingsManager()

        # ── Resolution ────────────────────────────────────────────────────────
        self.qual_combo = QComboBox()
        self.qual_combo.setStyleSheet(COMBO_STYLE)
        self.qual_combo.addItems(["1080p (FHD)", "720p (HD)", "4K (UHD)"])
        res = settings.get("export_resolution", "1080p")
        self.qual_combo.setCurrentIndex({"1080p": 0, "720p": 1, "4K": 2}.get(res, 0))
        layout.addLayout(self._row("Resolution:", self.qual_combo))

        # ── Frame Rate ────────────────────────────────────────────────────────
        self.fps_combo = QComboBox()
        self.fps_combo.setStyleSheet(COMBO_STYLE)
        self.fps_combo.addItems(["24 FPS", "30 FPS", "60 FPS"])
        fps = settings.get("export_fps", 30)
        self.fps_combo.setCurrentIndex({24: 0, 30: 1, 60: 2}.get(fps, 1))
        layout.addLayout(self._row("Frame Rate:", self.fps_combo))

        # ── Format ────────────────────────────────────────────────────────────
        self.fmt_combo = QComboBox()
        self.fmt_combo.setStyleSheet(COMBO_STYLE)
        self.fmt_combo.addItems(["MP4", "MOV"])
        fmt = settings.get("export_format", "mp4").upper()
        self.fmt_combo.setCurrentIndex(1 if fmt == "MOV" else 0)
        layout.addLayout(self._row("Format:", self.fmt_combo))

    @staticmethod
    def _row(label: str, widget: QComboBox) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        lbl = QLabel(label)
        lbl.setStyleSheet(LABEL_STYLE)
        row.addWidget(lbl)
        row.addWidget(widget, 1)  # combo takes remaining width
        return row

    # ── Getters ───────────────────────────────────────────────────────────────

    def get_resolution(self) -> str:
        return self.qual_combo.currentText()

    def get_fps(self) -> int:
        text = self.fps_combo.currentText()
        return int(text.split(" ")[0])

    def get_format(self) -> str:
        return self.fmt_combo.currentText().lower()

    def set_enabled(self, state: bool):
        self.qual_combo.setEnabled(state)
        self.fps_combo.setEnabled(state)
        self.fmt_combo.setEnabled(state)
