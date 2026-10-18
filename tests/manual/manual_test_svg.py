import sys
from PySide6.QtGui import QPixmap, QImage, QPainter
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)

# Test SVG generation and pixmap loading
from components.write_to_image.image_renderer import render_text_to_image
path = render_text_to_image("مرحبا بك", "Arial", 48, "#000", "test1234")
print("Saved SVG to:", path)

pm = QPixmap(path)
print("Pixmap size:", pm.width(), "x", pm.height())
