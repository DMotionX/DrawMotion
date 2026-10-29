"""
Settings page components base class + ProjectSettings.
Redesigned with card-based layout, proper spacing, and no default path shown.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit,
    QPushButton, QFileDialog, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QColor
from core.settings_manager import SettingsManager


# ── Shared stylesheet ─────────────────────────────────────────────────────────
SETTINGS_STYLE = """
    QWidget {
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        color: #D0D8D4;
    }
    QLabel {
        background-color: transparent;
        border: none;
    }
    /* Cards */
    QFrame#card {
        background-color: #192420;
        border: 1px solid #253530;
        border-radius: 12px;
    }
    /* Input widgets */
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
        background-color: #111D18;
        color: #D0D8D4;
        border: 1px solid #2E5040;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 13px;
        min-width: 220px;
        min-height: 38px;
        selection-background-color: #2E8B57;
    }
    QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover {
        border: 1px solid #3CB371;
        background-color: #152018;
    }
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
        border: 2px solid #3CB371;
        background-color: #111D18;
    }
    QComboBox::drop-down { border: none; width: 28px; }
    QComboBox::down-arrow { width: 10px; height: 10px; }
    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
        background-color: transparent;
        border: none;
        width: 24px;
        border-radius: 0 8px 8px 0;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover,
    QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
        background-color: #253530;
    }
    /* Checkbox */
    QCheckBox {
        color: #D0D8D4;
        font-size: 14px;
        spacing: 12px;
    }
    QCheckBox::indicator {
        width: 20px; height: 20px;
        border: 2px solid #2E5040;
        border-radius: 6px;
        background-color: #111D18;
    }
    QCheckBox::indicator:checked {
        background-color: #2E8B57;
        border: 2px solid #2E8B57;
    }
    QCheckBox::indicator:hover { border: 2px solid #3CB371; }
    /* Buttons */
    QPushButton {
        background-color: #2E8B57;
        color: white;
        font-size: 13px;
        font-weight: bold;
        border-radius: 8px;
        padding: 8px 20px;
        min-height: 38px;
        border: none;
    }
    QPushButton:hover  { background-color: #38A169; }
    QPushButton:pressed { background-color: #276749; }
    QPushButton#ghost {
        background-color: transparent;
        border: 1px solid #2E8B57;
        color: #2E8B57;
    }
    QPushButton#ghost:hover {
        background-color: rgba(46, 139, 87, 0.1);
        border: 1px solid #3CB371;
        color: #3CB371;
    }
"""


def make_card(parent=None):
    """Create a styled card frame."""
    card = QFrame(parent)
    card.setObjectName("card")
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(20)
    shadow.setColor(QColor(0, 0, 0, 60))
    shadow.setOffset(0, 4)
    card.setGraphicsEffect(shadow)
    return card


def section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "font-size: 18px; font-weight: 700; color: #2E8B57; "
        "padding-bottom: 4px; background: transparent; border: none;"
    )
    return lbl


def row_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFixedWidth(200)
    lbl.setStyleSheet("color: #7A9E90; font-size: 13px; background: transparent; border: none;")
    return lbl


def divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet("background-color: #253530; max-height: 1px; border: none;")
    return line


class SettingsSection(QWidget):
    """Base class for all settings sections."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = SettingsManager()
        self.setStyleSheet(SETTINGS_STYLE)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(40, 40, 40, 40)
        self._main_layout.setSpacing(24)
        self._main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Public layout alias — cards go here
        self.layout = self._main_layout

    # ── Helpers ───────────────────────────────────────────────────────────────

    def begin_card(self, title: str) -> QVBoxLayout:
        """Add a titled card and return its inner layout."""
        card = make_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(18)

        card_layout.addWidget(section_title(title))
        card_layout.addWidget(divider())

        self._main_layout.addWidget(card)
        return card_layout

    def add_row(self, card_layout: QVBoxLayout, label_text: str, widget: QWidget):
        """Add a label + widget row inside a card layout."""
        row = QHBoxLayout()
        row.setSpacing(16)
        row.addWidget(row_label(label_text))
        row.addWidget(widget)
        row.addStretch()
        card_layout.addLayout(row)

    # Legacy alias so sub-classes that didn't pass card_layout still compile
    def add_title(self, text):
        self._main_layout.addWidget(section_title(text))
        self._main_layout.addWidget(divider())


# ── Project Settings ──────────────────────────────────────────────────────────

class ProjectSettings(SettingsSection):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Card 1: Auto-Save ─────────────────────────────────────────────────
        card1 = self.begin_card("Project Settings")

        # Enable Auto-Save checkbox
        self.autosave_check = QCheckBox("Enable Auto-Save")
        self.autosave_check.setChecked(self.settings.get("auto_save_enabled", False))
        self.autosave_check.stateChanged.connect(
            lambda v: self.settings.set("auto_save_enabled", bool(v))
        )
        card1.addWidget(self.autosave_check)

        # Auto-Save Interval
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(1, 60)
        self.autosave_interval.setSuffix(" min")
        self.autosave_interval.setLocale(QLocale(QLocale.Language.English))
        self.autosave_interval.setValue(self.settings.get("auto_save_interval", 5))
        self.autosave_interval.setEnabled(self.settings.get("auto_save_enabled", False))
        self.autosave_interval.valueChanged.connect(
            lambda v: self.settings.set("auto_save_interval", v)
        )
        self.autosave_check.toggled.connect(self.autosave_interval.setEnabled)
        self.add_row(card1, "Auto-Save Interval:", self.autosave_interval)

        # ── Card 2: Animation ─────────────────────────────────────────────────
        card2 = self.begin_card("Animation")

        self.hand_size_spin = QDoubleSpinBox()
        self.hand_size_spin.setRange(0.1, 10.0)
        self.hand_size_spin.setSingleStep(0.2)
        self.hand_size_spin.setLocale(QLocale(QLocale.Language.English))
        self.hand_size_spin.setValue(self.settings.get("hand_size", 2.0))
        self.hand_size_spin.valueChanged.connect(
            lambda v: self.settings.set("hand_size", v)
        )
        self.add_row(card2, "Pen Hand Scale:", self.hand_size_spin)

        self.drag_hand_size_spin = QDoubleSpinBox()
        self.drag_hand_size_spin.setRange(0.1, 10.0)
        self.drag_hand_size_spin.setSingleStep(0.2)
        self.drag_hand_size_spin.setLocale(QLocale(QLocale.Language.English))
        self.drag_hand_size_spin.setValue(self.settings.get("drag_hand_size", 2.2))
        self.drag_hand_size_spin.valueChanged.connect(
            lambda v: self.settings.set("drag_hand_size", v)
        )
        self.add_row(card2, "Placement Hand Scale (Beta):", self.drag_hand_size_spin)

        # ── Card 3: Default Save Folder ───────────────────────────────────────
        card3 = self.begin_card("Default Save Folder")

        saved_path = self.settings.get("default_project_path", "")

        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setMinimumWidth(320)

        if saved_path:
            self.path_edit.setText(saved_path)
        else:
            self.path_edit.setPlaceholderText("No folder selected — click Browse to set one")

        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._browse_path)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("ghost")
        clear_btn.setFixedWidth(80)
        clear_btn.clicked.connect(self._clear_path)

        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse_btn)
        path_row.addWidget(clear_btn)
        card3.addLayout(path_row)

        # ── Card 4: Default Export Folder ───────────────────────────────────────
        card4 = self.begin_card("Default Export Folder")

        export_path = self.settings.get("default_export_path", "")

        self.export_path_edit = QLineEdit()
        self.export_path_edit.setReadOnly(True)
        self.export_path_edit.setMinimumWidth(320)

        if export_path:
            self.export_path_edit.setText(export_path)
        else:
            self.export_path_edit.setPlaceholderText("No folder selected — click Browse to set one")

        export_browse_btn = QPushButton("Browse…")
        export_browse_btn.setFixedWidth(100)
        export_browse_btn.clicked.connect(self._browse_export_path)

        export_clear_btn = QPushButton("Clear")
        export_clear_btn.setObjectName("ghost")
        export_clear_btn.setFixedWidth(80)
        export_clear_btn.clicked.connect(self._clear_export_path)

        export_path_row = QHBoxLayout()
        export_path_row.setSpacing(10)
        export_path_row.addWidget(self.export_path_edit, 1)
        export_path_row.addWidget(export_browse_btn)
        export_path_row.addWidget(export_clear_btn)
        card4.addLayout(export_path_row)

        self._main_layout.addStretch()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _browse_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Default Projects Folder")
        if dir_path:
            self.settings.set("default_project_path", dir_path)
            self.path_edit.setText(dir_path)

    def _clear_path(self):
        self.settings.set("default_project_path", "")
        self.path_edit.clear()
        self.path_edit.setPlaceholderText("No folder selected — click Browse to set one")

    def _browse_export_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Default Export Folder")
        if dir_path:
            self.settings.set("default_export_path", dir_path)
            self.export_path_edit.setText(dir_path)

    def _clear_export_path(self):
        self.settings.set("default_export_path", "")
        self.export_path_edit.clear()
        self.export_path_edit.setPlaceholderText("No folder selected — click Browse to set one")
