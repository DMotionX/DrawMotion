"""
Voice Recorder Dialog: A modern, floating UI component for recording voiceovers.
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal
from utils.theme import THEME_COLORS

class VoiceRecorderDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.is_recording = False
        self.elapsed_seconds = 0
        
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 150)
        
        self._init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer_label)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        container = QDialog()
        container.setStyleSheet(f"""
            QDialog {{
                background-color: {THEME_COLORS['surface']};
                border-radius: 12px;
                border: 2px solid {THEME_COLORS['divider']};
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🎙️ Voice Recorder")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Timer Label
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.timer_label)
        
        # Buttons Layout
        btn_layout = QHBoxLayout()
        
        self.record_btn = QPushButton("Record")
        self.record_btn.setStyleSheet(self._get_btn_style("#F44336")) # Red
        self.record_btn.clicked.connect(self._toggle_record)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(self._get_btn_style(THEME_COLORS['text_secondary']))
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.record_btn)
        
        layout.addLayout(btn_layout)
        main_layout.addWidget(container)

    def _get_btn_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """

    def _toggle_record(self):
        if not self.is_recording:
            # Start Recording
            self.manager.start_recording()
            self.is_recording = True
            self.record_btn.setText("Stop & Save")
            self.record_btn.setStyleSheet(self._get_btn_style(THEME_COLORS['primary_green']))
            
            self.cancel_btn.setEnabled(False)
            
            self.elapsed_seconds = 0
            self.timer.start(1000)
        else:
            # Stop Recording
            self.timer.stop()
            self.manager.stop_recording()
            self.accept()

    def _update_timer_label(self):
        self.elapsed_seconds += 1
        mins, secs = divmod(self.elapsed_seconds, 60)
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")
