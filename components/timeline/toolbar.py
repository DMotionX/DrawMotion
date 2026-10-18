from PySide6.QtWidgets import QFrame, QHBoxLayout, QToolButton, QLabel, QWidget, QSizePolicy
from PySide6.QtCore import Qt, QSize, Signal
from utils.theme import THEME_COLORS
from utils.icons import get_icon

class TimelineToolbar(QFrame):
    record_requested = Signal()
    focus_mode_toggled = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TimelineToolbar")
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            #TimelineToolbar {{
                background-color: {THEME_COLORS['panel']};
                border-bottom: 1px solid {THEME_COLORS['divider']};
            }}
        """)
        self._init_ui()
        
    def _create_tool_button(self, text, icon_name, is_accent=False):
        btn = QToolButton()
        btn.setText(text)
        
        if is_accent:
            btn.setIcon(get_icon(icon_name, "#F44336"))
        else:
            btn.setIcon(get_icon(icon_name))
            
        btn.setIconSize(QSize(16, 16))
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        if is_accent:
            btn.setStyleSheet(f"""
                QToolButton {{
                    color: #F44336; 
                    background: rgba(244, 67, 54, 0.05); 
                    border: 1px solid rgba(244, 67, 54, 0.3); 
                    border-radius: 4px; 
                    padding: 4px 10px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QToolButton:hover {{
                    background: rgba(244, 67, 54, 0.15);
                    border: 1px solid #F44336;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QToolButton {{
                    color: {THEME_COLORS['text_secondary']}; 
                    background: transparent; 
                    border: none;
                    border-radius: 4px; 
                    padding: 4px 10px;
                    font-size: 11px;
                }}
                QToolButton:hover {{
                    color: {THEME_COLORS['text_primary']};
                    background: {THEME_COLORS['surface']};
                }}
            """)
        return btn

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)
        
        # Tools title (Optional, can be hidden)
        title = QLabel("TIMELINE TOOLS")
        title.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 9px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(title)
        
        # Divider
        div1 = QFrame()
        div1.setFrameShape(QFrame.Shape.VLine)
        div1.setStyleSheet(f"color: {THEME_COLORS['divider']};")
        layout.addWidget(div1)
        
        # Record Button
        self.record_btn = self._create_tool_button("Voice Record", "mic", is_accent=True)
        self.record_btn.clicked.connect(self.record_requested.emit)
        layout.addWidget(self.record_btn)
        
        layout.addStretch()
        
        # --- DIGITAL TIMER ---
        self.timer_lbl = QLabel("00:00.0 / 00:00.0")
        self.timer_lbl.setStyleSheet(f"""
            color: {THEME_COLORS['text_primary']};
            background: {THEME_COLORS['bg_secondary']};
            border: 1px solid {THEME_COLORS['divider']};
            border-radius: 4px;
            padding: 4px 12px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        layout.addWidget(self.timer_lbl)
        
        layout.addStretch()

        # Focus Mode (Master Collapse) Pill Button
        self._is_focused = False
        self.focus_btn = QToolButton()
        self.focus_btn.setText("Focus Mode")
        self.focus_btn.setIcon(get_icon("maximize", THEME_COLORS['text_primary']))
        self.focus_btn.setIconSize(QSize(14, 14))
        self.focus_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.focus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.focus_btn.setStyleSheet(f"""
            QToolButton {{
                color: {THEME_COLORS['text_primary']}; 
                background: {THEME_COLORS['surface']}; 
                border: 1px solid {THEME_COLORS['divider']}; 
                border-radius: 12px;  /* Pill shape */
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background: rgba(255, 255, 255, 0.05);
            }}
        """)
        self.focus_btn.clicked.connect(self.toggle_focus_mode)
        layout.addWidget(self.focus_btn)

    def toggle_focus_mode(self):
        self._is_focused = not self._is_focused
        if self._is_focused:
            self.focus_btn.setText("Show Timeline")
            self.focus_btn.setIcon(get_icon("minimize", THEME_COLORS['bg_main']))
            self.focus_btn.setStyleSheet(f"""
                QToolButton {{
                    color: {THEME_COLORS['bg_main']}; 
                    background: {THEME_COLORS['primary_green']}; 
                    border: none; 
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
        else:
            self.focus_btn.setText("Focus Mode")
            self.focus_btn.setIcon(get_icon("maximize", THEME_COLORS['text_primary']))
            self.focus_btn.setStyleSheet(f"""
                QToolButton {{
                    color: {THEME_COLORS['text_primary']}; 
                    background: {THEME_COLORS['surface']}; 
                    border: 1px solid {THEME_COLORS['divider']}; 
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QToolButton:hover {{
                    background: rgba(255, 255, 255, 0.05);
                }}
            """)
        self.focus_mode_toggled.emit(self._is_focused)

    def mouseDoubleClickEvent(self, event):
        # Double clicking anywhere empty triggers the focus mode toggle
        self.toggle_focus_mode()
        super().mouseDoubleClickEvent(event)
