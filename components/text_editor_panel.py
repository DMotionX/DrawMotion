from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QComboBox, QFontComboBox, QLabel,
                               QColorDialog, QGridLayout)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt, Signal
from utils.theme import THEME_COLORS

class TextEditorPanel(QWidget):
    """
    A Properties panel for Text Items.
    Allows changing font, size, color, and alignment of the text node.
    """
    text_changed = Signal(str)
    format_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item = None
        self.model = None
        
        # Block signals flag
        self._updating = False
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(15)
        
        # Font Row
        font_row = QHBoxLayout()
        font_row.setSpacing(10)
        
        combo_style = f"""
            QComboBox {{ 
                padding: 6px; 
                border-radius: 4px; 
                border: 1px solid {THEME_COLORS['border']}; 
                background: {THEME_COLORS['bg_secondary']}; 
                color: {THEME_COLORS['text_primary']}; 
                font-size: 13px; 
            }}
            QComboBox::drop-down {{
                width: 0px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
            }}
            QComboBox QAbstractItemView {{
                background: {THEME_COLORS['bg_secondary']};
                color: {THEME_COLORS['text_primary']};
                selection-background-color: #2196F3;
                selection-color: white;
                min-width: 120px;
                padding: 2px;
                border: 1px solid #455A64;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 28px;
                padding: 4px;
            }}
        """
        
        self.font_combo = QFontComboBox()
        self.font_combo.setStyleSheet(combo_style)
        self.font_combo.setEditable(False) # [PHASE 4 FIX]: Must be False so clicking the text opens it!
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        font_row.addWidget(self.font_combo, stretch=2)
        
        self.size_combo = QComboBox()
        self.size_combo.setStyleSheet(combo_style)
        self.size_combo.setEditable(False) # [PHASE 4 FIX]
        sizes = [str(x) for x in [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72, 96, 128, 144]]
        self.size_combo.addItems(sizes)
        self.size_combo.currentTextChanged.connect(self._on_size_changed)
        font_row.addWidget(self.size_combo, stretch=1)
        layout.addLayout(font_row)
        
        # Style Grid (B, I, U, Color, Alignments)
        grid = QGridLayout()
        grid.setSpacing(10)
        
        self.btn_bold = self._create_tool_btn("B", "font-weight: bold; font-family: serif;")
        self.btn_bold.setCheckable(True)
        self.btn_bold.clicked.connect(self._toggle_bold)
        
        self.btn_italic = self._create_tool_btn("I", "font-style: italic; font-family: serif;")
        self.btn_italic.setCheckable(True)
        self.btn_italic.clicked.connect(self._toggle_italic)
        
        self.btn_underline = self._create_tool_btn("U", "text-decoration: underline; font-family: serif;")
        self.btn_underline.setCheckable(True)
        self.btn_underline.clicked.connect(self._toggle_underline)
        
        self.btn_color = self._create_tool_btn("A", f"color: {THEME_COLORS['text_primary']}; font-weight: bold; border-bottom: 3px solid #ff5722;")
        self.btn_color.clicked.connect(self._choose_color)
        
        grid.addWidget(self.btn_bold, 0, 0)
        grid.addWidget(self.btn_italic, 0, 1)
        grid.addWidget(self.btn_underline, 0, 2)
        grid.addWidget(self.btn_color, 0, 3)
        
        # Row 2: Alignments
        self.btn_align_left = self._create_tool_btn("Left", "font-size: 12px;")
        self.btn_align_left.setFixedSize(60, 36)
        
        self.btn_align_center = self._create_tool_btn("Center", "font-size: 12px;")
        self.btn_align_center.setFixedSize(60, 36)
        
        self.btn_align_right = self._create_tool_btn("Right", "font-size: 12px;")
        self.btn_align_right.setFixedSize(60, 36)
        
        grid.addWidget(self.btn_align_left, 1, 0)
        grid.addWidget(self.btn_align_center, 1, 1)
        grid.addWidget(self.btn_align_right, 1, 2)
        
        layout.addLayout(grid)
        layout.addStretch()

    def _create_tool_btn(self, text, style):
        btn = QPushButton(text)
        btn.setFixedSize(36, 36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['bg_secondary']};
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 4px;
                color: {THEME_COLORS['text_primary']};
                font-size: 16px;
                {style}
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['surface']};
                border: 1px solid #2196F3;
            }}
            QPushButton:checked {{
                background-color: #2196F3;
                color: white;
            }}
        """)
        return btn

    def set_node(self, item):
        """Bind to a WriteToImageGraphicsItem and populate the editor."""
        self.item = item
        if not item or not hasattr(item, 'model'):
            self.model = None
            self.setEnabled(False)
            return
            
        self.model = item.model
        self.setEnabled(True)
        # [PHASE 4 FIX]: The parent (InspectorPanel) calls set_inputs_enabled(False) 
        # which disables these comboboxes directly. We must re-enable them explicitly!
        self.font_combo.setEnabled(True)
        self.size_combo.setEnabled(True)
        
        self._updating = True
        
        # Read font
        font = QFont(self.model.font_family, self.model.font_size)
        self.font_combo.setCurrentFont(font)
        self.size_combo.setCurrentText(str(int(self.model.font_size)))
        
        self.btn_bold.setChecked(getattr(self.model, 'is_bold', False))
        self.btn_italic.setChecked(getattr(self.model, 'is_italic', False))
        self.btn_underline.setChecked(getattr(self.model, 'is_underline', False))
        
        # Update Color indicator
        color = self.model.color
        self.btn_color.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME_COLORS['bg_secondary']};
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 4px;
                color: {THEME_COLORS['text_primary']};
                font-size: 16px;
                font-weight: bold; 
                border-bottom: 3px solid {color};
            }}
            QPushButton:hover {{
                background-color: {THEME_COLORS['surface']};
                border: 1px solid #2196F3;
            }}
        """)
        
        self._updating = False

    def _toggle_bold(self):
        if self._updating or not self.model: return
        self.model.is_bold = self.btn_bold.isChecked()
        self._trigger_update()

    def _toggle_italic(self):
        if self._updating or not self.model: return
        self.model.is_italic = self.btn_italic.isChecked()
        self._trigger_update()

    def _toggle_underline(self):
        if self._updating or not self.model: return
        self.model.is_underline = self.btn_underline.isChecked()
        self._trigger_update()

    def _trigger_update(self):
        if self.item and hasattr(self.item, 'update_text_properties'):
            self.item.update_text_properties()

    def _on_font_changed(self, font: QFont):
        if self._updating or not self.model: return
        self.model.font_family = font.family()
        self._trigger_update()

    def _on_size_changed(self, size_str):
        if self._updating or not self.model: return
        try:
            self.model.font_size = int(size_str)
            self._trigger_update()
        except ValueError:
            pass

    def _choose_color(self):
        if self._updating or not self.model: return
        color = QColorDialog.getColor(QColor(self.model.color), self)
        if color.isValid():
            self.model.color = color.name()
            # Update indicator
            self.btn_color.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME_COLORS['bg_secondary']};
                    border: 1px solid {THEME_COLORS['border']};
                    border-radius: 4px;
                    color: {THEME_COLORS['text_primary']};
                    font-size: 16px;
                    font-weight: bold; 
                    border-bottom: 3px solid {color.name()};
                }}
                QPushButton:hover {{
                    background-color: {THEME_COLORS['surface']};
                    border: 1px solid #2196F3;
                }}
            """)
            self._trigger_update()
