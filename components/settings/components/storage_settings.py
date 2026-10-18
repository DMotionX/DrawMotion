from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout, QMessageBox, QCheckBox, QComboBox
from PySide6.QtCore import Qt, QSettings
from utils.theme import THEME_COLORS

class StorageSettings(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # We will get the project_manager from main app later
        self.project_manager = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Storage & Cache")
        title.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("Manage the disk space used by saved projects and temporary cache files.")
        desc.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 14px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Storage & Cache content only

        # Cache Section
        self.cache_lbl = QLabel("Cache Size: Calculating...")
        self.cache_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.cache_lbl)

        clear_cache_btn = QPushButton("Clear Cache")
        clear_cache_btn.setStyleSheet(f"background-color: transparent; color: {THEME_COLORS['primary_green']}; border: 1px solid {THEME_COLORS['primary_green']}; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        clear_cache_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_cache_btn.clicked.connect(self._clear_cache)
        
        c_layout = QHBoxLayout()
        c_layout.addWidget(clear_cache_btn)
        c_layout.addStretch()
        layout.addLayout(c_layout)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {THEME_COLORS['divider']};")
        layout.addWidget(div)

        # Projects Section
        self.proj_lbl = QLabel("Projects Size: Calculating...")
        self.proj_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.proj_lbl)

        clear_proj_btn = QPushButton("Delete All Projects")
        clear_proj_btn.setStyleSheet(f"background-color: #ff5252; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        clear_proj_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_proj_btn.clicked.connect(self._clear_projects)
        
        p_layout = QHBoxLayout()
        p_layout.addWidget(clear_proj_btn)
        p_layout.addStretch()
        layout.addLayout(p_layout)

        layout.addStretch()

    # Removed duplicate auto save methods

    def set_project_manager(self, pm):
        self.project_manager = pm
        self.update_sizes()

    def update_sizes(self):
        if not self.project_manager: return
        cache_size = self.project_manager.get_cache_size() / (1024 * 1024)
        proj_size = self.project_manager.get_projects_size() / (1024 * 1024)
        self.cache_lbl.setText(f"Cache Size: {cache_size:.2f} MB")
        self.proj_lbl.setText(f"Projects Size: {proj_size:.2f} MB")

    def _clear_cache(self):
        if not self.project_manager: return
        if self.project_manager.clear_cache():
            QMessageBox.information(self, "Success", "Cache cleared successfully.")
            self.update_sizes()

    def _clear_projects(self):
        if not self.project_manager: return
        confirm = QMessageBox.question(self, "Delete All Projects", 
            "WARNING: This will permanently delete ALL your saved projects! This action cannot be undone. Are you absolutely sure?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            if self.project_manager.clear_all_projects():
                QMessageBox.information(self, "Success", "All projects have been deleted.")
                self.update_sizes()
