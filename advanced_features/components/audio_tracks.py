from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from utils.theme import THEME_COLORS

class AudioTrackComponent(QWidget):
    """Component for the Audio layer on the timeline"""
    def __init__(self, title="Audio", parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color: {THEME_COLORS['panel']}; border-radius: 4px; margin-bottom: 2px;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: bold;")
        
        self.record_btn = QPushButton("REC")
        self.record_btn.setFixedSize(24, 24)
        self.record_btn.setStyleSheet(f"background: transparent; color: red;")
        self.record_btn.setToolTip("Record / Add Audio")
        
        layout.addWidget(self.title_lbl)
        layout.addStretch()
        layout.addWidget(self.record_btn)

class SoundEffectTrackComponent(AudioTrackComponent):
    """Component for the Sound Effect layer on the timeline"""
    def __init__(self, parent=None):
        super().__init__(title="Sound Effect", parent=parent)
        self.record_btn.setText("SFX")
        self.record_btn.setStyleSheet(f"background: transparent; color: {THEME_COLORS['primary_green']};")
        self.record_btn.setToolTip("Add Sound Effect")
