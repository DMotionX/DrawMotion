from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QColorDialog, QFormLayout, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

class ProjectSettingsDialog(QDialog):
    def __init__(self, workspace, parent=None):
        super().__init__(parent)
        self.workspace = workspace
        self.setWindowTitle("Canvas Settings")
        self.setMinimumSize(400, 300)
        self.setStyleSheet("""
            QDialog { background-color: #1A211D; color: #FFFFFF; }
            QLabel { color: #FFFFFF; font-size: 13px; }
            QComboBox, QLineEdit {
                background-color: #222A27;
                color: #FFFFFF;
                border: 1px solid #2A322E;
                padding: 4px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #2E8B57;
                color: #FFFFFF;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #3CB371; }
            QPushButton#colorBtn {
                border: 2px solid #FFFFFF;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("Canvas & Resolution Settings")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        form = QFormLayout()
        
        # Aspect Ratio
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(["16:9 (Landscape)", "9:16 (Portrait)", "1:1 (Square)"])
        form.addRow("Aspect Ratio:", self.aspect_combo)
        
        # Resolution (Informational/Placeholder for now, mostly handled by export engine)
        self.res_combo = QComboBox()
        self.res_combo.addItems(["1920x1080 (FHD)", "1280x720 (HD)", "3840x2160 (4K)"])
        form.addRow("Resolution:", self.res_combo)
        
        # Background Color is temporarily hidden as per user feedback (requires SVG logic update)
        layout.addLayout(form)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #333333;")
        cancel_btn.clicked.connect(self.reject)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_settings)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(apply_btn)
        layout.addLayout(btn_layout)
        
    def _apply_settings(self):
        if not self.workspace:
            self.accept()
            return
            
        # Apply Aspect Ratio
        aspect = self.aspect_combo.currentText()
        w, h = 16, 9
        if "9:16" in aspect:
            w, h = 9, 16
        elif "1:1" in aspect:
            w, h = 1, 1
            
        for ab in self.workspace.artboards:
            ab._set_aspect_ratio(w, h)
            
        self.accept()

class ProjectInfoDialog(QDialog):
    def __init__(self, workspace, project_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Project Information")
        self.setFixedSize(350, 250)
        self.setStyleSheet("""
            QDialog { background-color: #1A211D; color: #FFFFFF; }
            QLabel { color: #FFFFFF; font-size: 13px; }
            QLabel#title { font-size: 16px; font-weight: bold; color: #2E8B57; }
            QPushButton {
                background-color: #2E8B57;
                color: #FFFFFF;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #3CB371; }
        """)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("Project Information")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Calculate stats
        scene_count = len(workspace.artboards) if workspace else 0
        item_count = len(workspace.user_items) if workspace else 0
        audio_count = len(workspace.audio_items) if workspace else 0
        
        form = QFormLayout()
        form.addRow("Scenes Count:", QLabel(str(scene_count)))
        form.addRow("Visual Elements:", QLabel(str(item_count)))
        form.addRow("Audio Tracks:", QLabel(str(audio_count)))
        
        layout.addLayout(form)
        layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
