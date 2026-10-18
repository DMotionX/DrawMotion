from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QFormLayout, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtMultimedia import QMediaDevices
from core.settings_manager import SettingsManager
from utils.theme import THEME_COLORS

class AudioSettingsDialog(QDialog):
    def __init__(self, parent=None, workspace=None):
        super().__init__(parent)
        self.workspace = workspace
        self.setWindowTitle("Audio Settings")
        self.setFixedSize(380, 260)
        self.setStyleSheet(f"""
            QDialog {{ background-color: #1A211D; color: #FFFFFF; }}
            QLabel {{ color: #FFFFFF; font-size: 13px; }}
            QComboBox {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                color: #FFFFFF;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: #1A211D;
                color: #FFFFFF;
                selection-background-color: {THEME_COLORS['primary_green']};
                selection-color: #FFFFFF;
            }}
            QPushButton {{
                background-color: {THEME_COLORS['primary_green']};
                color: #FFFFFF;
                padding: 8px 18px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #3CB371; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Audio & Device Settings")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        # Audio Output Device Selector
        self.device_combo = QComboBox()
        self._populate_devices()
        form.addRow("Output Device:", self.device_combo)
        
        # Master Volume
        self.master_volume = QSlider(Qt.Orientation.Horizontal)
        self.master_volume.setRange(0, 100)
        saved_master = SettingsManager().get("master_volume", 100)
        self.master_volume.setValue(int(saved_master))
        form.addRow("Master Volume:", self.master_volume)
        
        layout.addLayout(form)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #333333;")
        cancel_btn.clicked.connect(self.reject)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._on_apply)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(apply_btn)
        layout.addLayout(btn_layout)

    def _populate_devices(self):
        devices = QMediaDevices.audioOutputs()
        saved_desc = SettingsManager().get("audio_output_device", "")
        
        selected_idx = 0
        preferred_idx = -1
        
        for idx, dev in enumerate(devices):
            desc = dev.description()
            self.device_combo.addItem(desc, desc)
            if saved_desc and desc == saved_desc:
                selected_idx = idx
            elif preferred_idx == -1 and any(k in desc.lower() for k in ["headphone", "earphone", "headset"]):
                preferred_idx = idx
                
        if not saved_desc and preferred_idx != -1:
            selected_idx = preferred_idx
            
        if self.device_combo.count() > 0:
            self.device_combo.setCurrentIndex(selected_idx)

    def _on_apply(self):
        chosen_device = self.device_combo.currentData()
        SettingsManager().set("audio_output_device", chosen_device)
        SettingsManager().set("master_volume", self.master_volume.value())
        
        # Apply to workspace engines if present
        if self.workspace:
            if hasattr(self.workspace, 'audio_engine'):
                self.workspace.audio_engine.set_output_device(chosen_device)
            if hasattr(self.workspace, 'animator_engine') and hasattr(self.workspace.animator_engine, 'sfx_engine'):
                self.workspace.animator_engine.sfx_engine.set_output_device(chosen_device)
                
        self.accept()
