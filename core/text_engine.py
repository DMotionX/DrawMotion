"""
Purpose: Converts Text and Strings into QPainterPaths for the animation engine.
Features: Uses QPainterPath.addText to generate accurate vector boundaries of text based on font and size.
"""
from PySide6.QtGui import QPainterPath, QFont
from PySide6.QtCore import QPointF

class TextEngine:
    @staticmethod
    def text_to_path(text: str, font_family: str = "Segoe UI", font_size: int = 100) -> QPainterPath:
        """
        Converts a given string to a vector QPainterPath using the specified font.
        """
        path = QPainterPath()
        font = QFont(font_family, font_size)
        font.setBold(True) # Bold looks better for whiteboard drawing outlines
        
        # addText adds the text outline to the path
        # The baseline is at Y=0, so the text goes upwards. 
        # We can translate it later in the item itself.
        path.addText(QPointF(0, 0), font, text)
        
        # Simplify path removes overlapping segments and makes it cleaner
        return path.simplified()
