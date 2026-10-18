from PySide6.QtWidgets import QComboBox
from .project_settings import SettingsSection


class ExportSettings(SettingsSection):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Card 1: Video Output ──────────────────────────────────────────────
        card1 = self.begin_card("Video Output")

        self.res_combo = QComboBox()
        self.res_combo.addItems(["720p", "1080p", "4K"])
        self.res_combo.setCurrentText(self.settings.get("export_resolution", "1080p"))
        self.res_combo.currentTextChanged.connect(
            lambda v: self.settings.set("export_resolution", v)
        )
        self.add_row(card1, "Resolution:", self.res_combo)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["24", "30", "60"])
        self.fps_combo.setCurrentText(str(self.settings.get("export_fps", 30)))
        self.fps_combo.currentTextChanged.connect(
            lambda v: self.settings.set("export_fps", int(v))
        )
        self.add_row(card1, "Frame Rate (FPS):", self.fps_combo)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "avi", "mov"])
        self.format_combo.setCurrentText(self.settings.get("export_format", "mp4"))
        self.format_combo.currentTextChanged.connect(
            lambda v: self.settings.set("export_format", v)
        )
        self.add_row(card1, "Video Format:", self.format_combo)

        self._main_layout.addStretch()
