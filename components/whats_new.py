from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import Qt
from utils.theme import THEME_COLORS

class WhatsNewDialog(QDialog):
    def __init__(self, version, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"What's New in v{version}")
        self.setFixedSize(600, 400)
        self.setStyleSheet(f"background-color: {THEME_COLORS['bg_main']}; color: {THEME_COLORS['text_primary']};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        title = QLabel(f"Welcome to DrawMotion v{version}! 🚀")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {THEME_COLORS['primary_green']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Release Notes (Ideally fetched or hardcoded for the current release)
        notes = QTextEdit()
        notes.setReadOnly(True)
        notes.setStyleSheet(f"""
            QTextEdit {{
                background-color: {THEME_COLORS['surface']};
                border: 1px solid {THEME_COLORS['divider']};
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }}
        """)
        
        # Mocking release notes based on the current planned changes
        release_notes = f"""<h2>What's New in v{version}</h2>
        <h3>✨ New Features & Improvements</h3>
        <ul>
            <li><b>Timeline Auto-Scroll:</b> Added a smart auto-scroll feature to the timeline. Dragging elements to the screen's edge now seamlessly scrolls the timeline, offering limitless editing freedom.</li>
            <li><b>Timeline UX Polish:</b> Repositioned the delete (X) button on audio tracks to the left side, eliminating overlap with resize handles for more precise control.</li>
            <li><b>Smart Default Paths:</b> DrawMotion now automatically detects your system and sets your "Documents" folder as the default path for Projects and Exports immediately upon installation.</li>
            <li><b>Settings UI:</b> Added missing professional icons to the Storage and Updates sections in the settings sidebar.</li>
        </ul>
        <h3>🐛 Bug Fixes & Stability</h3>
        <ul>
            <li><b>Silent Updater Restart:</b> Fixed an issue where the silent updater failed to reopen the application automatically after a background update. DrawMotion will now seamlessly restart to continue your work without interruption.</li>
        </ul>
        <br><br>
        <i>Thank you for using DrawMotion Studio!</i>
        """
        notes.setHtml(release_notes)
        layout.addWidget(notes)
        
        # OK Button
        btn = QPushButton("Awesome! Let's Go")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['primary_green']};
                color: {THEME_COLORS['bg_main']};
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #3bcf85;
            }}
        """)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
