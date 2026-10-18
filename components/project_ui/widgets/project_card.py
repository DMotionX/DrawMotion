"""
Project Card Widget — represents a single project in the list.
"""
import os
import platform
import subprocess
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from utils.theme import THEME_COLORS

class ProjectCard(QFrame):
    project_deleted = Signal(str)  # Emits project_id
    project_loaded = Signal(dict)

    def __init__(self, proj_data, project_manager, parent=None):
        super().__init__(parent)
        self.proj_data = proj_data
        self.project_manager = project_manager
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_COLORS['surface']};
                border-radius: 8px;
                border: 1px solid {THEME_COLORS['divider']};
            }}
            QFrame:hover {{
                background-color: {THEME_COLORS['bg_secondary']};
                border: 1px solid {THEME_COLORS['primary_green']};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        # Details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(4)
        
        name_lbl = QLabel(self.proj_data['name'])
        name_lbl.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {THEME_COLORS['text_primary']}; border: none; background: transparent;")
        
        info_text = f"Created: {self.proj_data['created_at'][:10]}"
        
        # Add file size if path exists
        if os.path.exists(self.proj_data['path']):
            size_mb = os.path.getsize(self.proj_data['path']) / (1024 * 1024)
            info_text += f"  •  Size: {size_mb:.1f} MB"
            
        info_lbl = QLabel(info_text)
        info_lbl.setStyleSheet(f"font-size: 11px; color: {THEME_COLORS['text_secondary']}; border: none; background: transparent;")
        
        details_layout.addWidget(name_lbl)
        details_layout.addWidget(info_lbl)

        # Buttons
        load_btn = QPushButton("Load")
        load_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['primary_green']};
                color: white;
                font-weight: bold;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: #38A169; }}
        """)
        load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        load_btn.clicked.connect(self._on_load)

        open_btn = QPushButton("Open Folder")
        open_btn.setToolTip("Open Folder Location")
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {THEME_COLORS['divider']};
                padding: 6px 10px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {THEME_COLORS['divider']}; }}
        """)
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self._on_open_location)

        del_btn = QPushButton("Delete")
        del_btn.setToolTip("Delete Project")
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid #ff5252;
                padding: 6px 10px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: rgba(255, 82, 82, 0.1); }}
        """)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(self._on_delete)

        layout.addLayout(details_layout)
        layout.addStretch()
        layout.addWidget(load_btn)
        layout.addWidget(open_btn)
        layout.addWidget(del_btn)

    def _on_load(self):
        self.project_loaded.emit(self.proj_data)

    def _on_open_location(self):
        path = self.proj_data['path']
        if os.path.exists(path):
            folder = os.path.dirname(path)
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        else:
            QMessageBox.warning(self, "Not Found", "The project folder could not be found.")

    def _on_delete(self):
        confirm = QMessageBox.question(
            self, "Delete Project", 
            f"Are you sure you want to delete '{self.proj_data['name']}'?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            if self.project_manager.delete_project(self.proj_data['id']):
                self.project_deleted.emit(self.proj_data['id'])
