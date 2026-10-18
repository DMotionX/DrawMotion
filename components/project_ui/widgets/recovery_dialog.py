"""
Crash Recovery Dialog — Professional dialog to handle unsaved sessions.
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
from utils.theme import THEME_COLORS

DIALOG_STYLE = f"""
    QDialog {{
        background-color: {THEME_COLORS['bg_main']};
        color: {THEME_COLORS['text_primary']};
        font-family: 'Segoe UI', Arial, sans-serif;
    }}
"""

BTN_PRIMARY = f"""
    QPushButton {{
        background-color: {THEME_COLORS['primary_green']};
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px 24px;
        border-radius: 6px;
        font-size: 14px;
    }}
    QPushButton:hover {{ background-color: #38A169; }}
"""

BTN_SECONDARY = f"""
    QPushButton {{
        background-color: transparent;
        color: {THEME_COLORS['text_secondary']};
        border: 1px solid {THEME_COLORS['divider']};
        padding: 10px 24px;
        border-radius: 6px;
        font-size: 14px;
    }}
    QPushButton:hover {{ 
        background-color: {THEME_COLORS['bg_secondary']};
        color: {THEME_COLORS['text_primary']};
    }}
"""

class CrashRecoveryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crash Recovery")
        self.setFixedSize(500, 200)
        self.setStyleSheet(DIALOG_STYLE)
        
        # Remove the '?' button from the title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Header Row (Icon + Text)
        header_row = QHBoxLayout()
        header_row.setSpacing(16)
        
        icon_lbl = QFrame()
        icon_lbl.setFixedSize(48, 48)
        icon_lbl.setStyleSheet("""
            QFrame {
                background-color: #E65100;
                border-radius: 10px;
                border: none;
            }
        """)
        icon_inner_layout = QVBoxLayout(icon_lbl)
        icon_inner_layout.setContentsMargins(0, 0, 0, 0)
        icon_inner_text = QLabel("!")
        icon_inner_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_inner_text.setStyleSheet("color: white; font-size: 22px; font-weight: bold; background: transparent; border: none;")
        icon_inner_layout.addWidget(icon_inner_text)
        
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        
        title = QLabel("Unsaved Project Found")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        subtitle = QLabel("It looks like DrawMotion was closed unexpectedly.\nWould you like to restore your previous session?")
        subtitle.setStyleSheet(f"font-size: 13px; color: {THEME_COLORS['text_secondary']};")
        
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        text_col.addStretch()
        
        header_row.addWidget(icon_lbl)
        header_row.addLayout(text_col)
        header_row.addStretch()
        
        layout.addLayout(header_row)
        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        
        discard_btn = QPushButton("Discard & Start Fresh")
        discard_btn.setStyleSheet(BTN_SECONDARY)
        discard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        discard_btn.clicked.connect(self.reject)
        
        restore_btn = QPushButton("Restore Project")
        restore_btn.setStyleSheet(BTN_PRIMARY)
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.clicked.connect(self.accept)
        
        btn_row.addStretch()
        btn_row.addWidget(discard_btn)
        btn_row.addWidget(restore_btn)
        
        layout.addLayout(btn_row)
