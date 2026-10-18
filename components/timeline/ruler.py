from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Signal, Qt
from utils.theme import THEME_COLORS

class TimeRuler(QWidget):
    time_seek = Signal(float)
    
    def __init__(self, pixels_per_second=50):
        super().__init__()
        self.pixels_per_second = pixels_per_second
        self.setFixedHeight(24)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor(THEME_COLORS['text_secondary']))
        pen.setWidth(1)
        painter.setPen(pen)
        
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        
        width = self.width()
        max_seconds = int(width / self.pixels_per_second) + 1
        
        for sec in range(max_seconds + 1):
            x = sec * self.pixels_per_second
            if sec % 2 == 0:
                painter.drawLine(x, 14, x, 24)
                m, s = divmod(sec, 60)
                time_str = f"{m:02d}:{s:02d}"
                painter.drawText(x + 3, 12, time_str)
            else:
                painter.drawLine(x, 18, x, 24)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._emit_seek(event.pos().x())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._emit_seek(event.pos().x())
            
    def _emit_seek(self, x_pos):
        time_sec = max(0.0, x_pos / self.pixels_per_second)
        self.time_seek.emit(time_sec)
