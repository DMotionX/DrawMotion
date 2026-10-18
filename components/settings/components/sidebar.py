from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy
from PySide6.QtCore import Signal, Qt, QSize
from utils.icons import get_icon

class SettingsSidebar(QWidget):
    """
    Sidebar for navigating between different settings sections.
    """
    section_selected = Signal(int) # Emits the index of the selected section

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setStyleSheet("""
            QWidget {
                background-color: #1E2522;
                border-right: 1px solid #2E8B57;
            }
            QPushButton {
                background-color: transparent;
                color: #A0AAB2;
                border: none;
                text-align: left;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                margin: 4px 8px;
            }
            QPushButton:hover {
                background-color: #2A3631;
                color: white;
            }
            QPushButton:checked {
                background-color: #2E8B57;
                color: white;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 20, 0, 20)
        self.layout.setSpacing(5)

        self.buttons = []
        
        # Sections Definition
        sections = [
            ("folder", "Project Settings"),
            ("edit", "Drawing & Animation"),
            ("upload", "Export Settings"),
            ("settings", "General Settings"),
            ("box", "Storage & Cache"),
            ("download", "Updates")
        ]

        for i, (icon_name, text) in enumerate(sections):
            btn = QPushButton(f"  {text}")
            btn.setIcon(get_icon(icon_name, "#A0AAB2"))
            btn.setIconSize(QSize(18, 18))
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 15px;
                }
            """)
            
            btn.setProperty("section_idx", i)
            btn.clicked.connect(self._on_sidebar_button_clicked)
            
            self.layout.addWidget(btn)
            self.buttons.append(btn)

        self.layout.addStretch()

        # Select first section by default
        if self.buttons:
            self._on_button_clicked(0)

    def _on_sidebar_button_clicked(self):
        sender = self.sender()
        if sender:
            idx = sender.property("section_idx")
            if idx is not None:
                self._on_button_clicked(idx)

    def _on_button_clicked(self, index):
        icon_names = ["folder", "pen", "upload", "settings", "box", "download"]
        for i, btn in enumerate(self.buttons):
            if i == index:
                btn.setChecked(True)
                btn.setIcon(get_icon(icon_names[i], "#FFFFFF"))
            else:
                btn.setChecked(False)
                btn.setIcon(get_icon(icon_names[i], "#A0AAB2"))
        self.section_selected.emit(index)
