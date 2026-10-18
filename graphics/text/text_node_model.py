import uuid
import re
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import QPointF, QRectF, Qt

class TextNodeModel:
    """
    Data Model for the Interactive Text Node.
    Completely decoupled from the View (UI) and the Bridge Engine.
    """
    def __init__(self, text: str = "", position: QPointF = QPointF(0, 0)):
        self.id = str(uuid.uuid4())
        self.text = text
        
        # Styling
        self.font_family = "Arial"
        self.font_size = 24
        self.font_weight = QFont.Weight.Normal
        self.is_italic = False
        self.color = QColor("#000000")
        
        # Spatial
        self.position = position
        self.rotation = 0.0
        self.scale = 1.0
        self.fixed_width = -1  # For Area Text (paragraph word-wrapping), -1 means Point Text
        self.bounding_rect = QRectF(0, 0, 100, 50)
        
        # Semantic & Layout
        self.alignment = Qt.AlignmentFlag.AlignLeft
        self.language = self._detect_language(text)
        
    def _detect_language(self, text: str) -> str:
        if not text:
            return "en"
        # Simple heuristic: If it contains Arabic characters, treat as Arabic (RTL)
        arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]')
        if arabic_pattern.search(text):
            return "ar"
        return "en"
        
    def update_text(self, new_text: str):
        self.text = new_text
        self.language = self._detect_language(self.text)
        
        # Auto-align based on language if not explicitly overridden
        if self.language == "ar":
            self.alignment = Qt.AlignmentFlag.AlignRight
        else:
            self.alignment = Qt.AlignmentFlag.AlignLeft
            
    def get_font(self) -> QFont:
        font = QFont(self.font_family, self.font_size, self.font_weight)
        font.setItalic(self.is_italic)
        return font

    def get_semantic_type(self) -> str:
        """
        Analyzes the text to determine its role for the Bridge Engine.
        """
        if not self.text:
            return "body"
            
        # Check for equations (+ - * = /)
        if any(c in "+-*/=" for c in self.text) and not any(c.isalpha() for c in self.text):
            return "equation"
            
        # Check if it's a short title
        if len(self.text) < 25 and "\n" not in self.text:
            return "title"
            
        return "body"
        
    def export_to_writing_payload(self) -> dict:
        """
        Exports a clean dictionary payload ready for the Bridge Engine to consume,
        without passing any Qt Graphics Items.
        """
        return {
            "type": "text",
            "text": self.text,
            "font": self.get_font(),
            "color": self.color.name(),
            "pos": self.position,
            "rotation": self.rotation,
            "scale": self.scale,
            "direction": "RTL" if self.language == "ar" else "LTR",
            "semantic": self.get_semantic_type(),
            "priority": "medium" if self.get_semantic_type() == "body" else "high"
        }
