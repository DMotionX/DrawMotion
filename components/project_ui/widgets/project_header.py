"""
Project Header Widget — Title and main actions (New Project, Open File).
"""
import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from utils.theme import THEME_COLORS

class ProjectHeader(QWidget):
    open_file_requested = Signal(str) # Emits the selected file path
    new_project_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_lbl = QLabel("My Projects")
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {THEME_COLORS['text_primary']};")
        
        layout.addWidget(title_lbl)
        layout.addStretch()

        # New Project Button
        self.new_project_btn = QPushButton("New Project")
        self.new_project_btn.setToolTip("Start a fresh empty project")
        self.new_project_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['primary_green']};
                color: white;
                font-weight: bold;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: #38A169; }}
        """)
        self.new_project_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_project_btn.clicked.connect(self.new_project_requested.emit)
        
        layout.addWidget(self.new_project_btn)
        layout.addSpacing(10)
        
        # Open File Button

        self.open_file_btn = QPushButton("Open File...")
        self.open_file_btn.setToolTip("Open a .wip project file from your computer")
        self.open_file_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {THEME_COLORS['text_primary']};
                border: 1px solid {THEME_COLORS['divider']};
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {THEME_COLORS['divider']}; }}
        """)
        self.open_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_file_btn.clicked.connect(self._on_open_file)
        
        layout.addWidget(self.open_file_btn)

    def _on_open_file(self):
        from core.settings_manager import SettingsManager
        default_dir = SettingsManager().get("default_project_path", "")
        if not default_dir or not os.path.exists(default_dir):
            default_dir = os.path.expanduser("~")
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project File", 
            default_dir, 
            "DrawMotion Projects (*.wip)"
        )
        if file_path:
            self.open_file_requested.emit(file_path)
