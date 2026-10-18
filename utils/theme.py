"""
Purpose: Centralized Theme Manager for the DrawMotion application.
Features: Defines color palette constants and provides a global, highly polished QSS stylesheet matching the original design.
"""
from PySide6.QtGui import QFontDatabase, QFont

THEME_COLORS = {
    "bg_main": "#121614",
    "bg_secondary": "#181C1A",
    "panel": "#1E2421",
    "border": "#2A322E",
    "divider": "#323A36",
    "primary_green": "#2E8B57",
    "green_hover": "#3FA36D",
    "purple_accent": "#8B5CF6",
    "purple_hover": "#A855F7",
    "orange_action": "#F28C28",
    "orange_hover": "#FF9F3F",
    "canvas": "#FAFAF8",
    "surface": "#222A27",
    "text_primary": "#F5F5F5",
    "text_secondary": "#A6ABA8",
}

def get_global_qss() -> str:
    return f"""
        * {{
            font-family: "Segoe UI", "Inter", sans-serif;
            font-size: 12px;
        }}
        QMainWindow, QWidget {{
            background-color: {THEME_COLORS['bg_main']};
            color: {THEME_COLORS['text_primary']};
        }}
        QLabel, QCheckBox, QRadioButton {{
            background-color: transparent;
        }}
        
        /* Panels */
        QFrame#TopBar, QFrame#LeftPanel, QFrame#RightPanel, QFrame#BottomPanel {{
            background-color: {THEME_COLORS['panel']};
            border: 1px solid {THEME_COLORS['border']};
            border-radius: 8px;
        }}
        
        /* Tool Buttons (Top Bar) */
        QToolButton {{
            background-color: transparent;
            color: {THEME_COLORS['text_secondary']};
            border: none;
            border-radius: 6px;
            padding: 6px;
            min-width: 48px;
        }}
        QToolButton:hover {{
            background-color: {THEME_COLORS['border']};
            color: {THEME_COLORS['text_primary']};
        }}
        QToolButton:checked {{
            background-color: {THEME_COLORS['surface']};
            color: {THEME_COLORS['primary_green']};
        }}
        
        /* Standard Buttons */
        QPushButton {{
            background-color: {THEME_COLORS['surface']};
            color: {THEME_COLORS['text_primary']};
            border: 1px solid {THEME_COLORS['border']};
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {THEME_COLORS['divider']};
        }}
        
        /* Export Button (Orange) */
        QToolButton#ExportButton, QPushButton#ExportButton {{
            background-color: {THEME_COLORS['orange_action']};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }}
        QToolButton#ExportButton:hover, QPushButton#ExportButton:hover {{
            background-color: {THEME_COLORS['orange_hover']};
        }}
        
        /* Inputs */
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
            background-color: {THEME_COLORS['bg_main']};
            color: {THEME_COLORS['text_primary']};
            border: 1px solid {THEME_COLORS['divider']};
            border-radius: 4px;
            padding: 4px 8px;
            min-height: 20px;
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {THEME_COLORS['primary_green']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {THEME_COLORS['surface']};
            color: {THEME_COLORS['text_primary']};
            selection-background-color: {THEME_COLORS['primary_green']};
            border: 1px solid {THEME_COLORS['border']};
            outline: 0px;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 8px;
        }}
        
        /* Sliders */
        QSlider::groove:horizontal {{
            border: none;
            height: 4px;
            background: {THEME_COLORS['divider']};
            border-radius: 2px;
        }}
        QSlider::sub-page:horizontal {{
            background: {THEME_COLORS['primary_green']};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {THEME_COLORS['text_primary']};
            border: none;
            width: 12px;
            margin-top: -4px;
            margin-bottom: -4px;
            border-radius: 6px;
        }}
        
        /* Scrollbars */
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {THEME_COLORS['border']};
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        
        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: {THEME_COLORS['border']};
            border-radius: 4px;
            min-width: 20px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            background: {THEME_COLORS['divider']};
            border-radius: 3px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
            background: {THEME_COLORS['text_secondary']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
            height: 0px;
            width: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: none;
            background: transparent;
        }}
        QTabBar {{
            background: transparent;
        }}
        QTabBar::tab {{
            background: transparent;
            color: {THEME_COLORS['text_secondary']};
            padding: 8px 12px;
            border: none;
            border-bottom: 2px solid transparent;
            font-weight: bold;
        }}
        QTabBar::tab:selected {{
            color: {THEME_COLORS['primary_green']};
            border-bottom: 2px solid {THEME_COLORS['primary_green']};
        }}
        QTabBar::tab:hover {{
            color: {THEME_COLORS['text_primary']};
        }}
        
        /* Vertical Tabs (Left Panel) */
        QTabBar[shape="2"]::tab, QTabBar[shape="3"]::tab {{
            padding: 12px;
            border-bottom: none;
            border-left: 2px solid transparent;
        }}
        QTabBar[shape="2"]::tab:selected, QTabBar[shape="3"]::tab:selected {{
            border-bottom: none;
            border-left: 2px solid {THEME_COLORS['primary_green']};
            background-color: {THEME_COLORS['bg_secondary']};
        }}
        
        /* List Widget */
        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
        }}
        QListWidget::item {{
            padding: 8px;
            border-radius: 4px;
            color: {THEME_COLORS['text_secondary']};
        }}
        QListWidget::item:hover {{
            background-color: {THEME_COLORS['bg_secondary']};
            color: {THEME_COLORS['text_primary']};
        }}
        QListWidget::item:selected {{
            background-color: {THEME_COLORS['bg_main']};
            color: {THEME_COLORS['text_primary']};
            border: 1px solid {THEME_COLORS['border']};
        }}
    """
