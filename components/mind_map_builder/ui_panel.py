from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame)
from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor
from utils.theme import THEME_COLORS

class DraggableTemplate(QFrame):
    clicked = Signal(str)
    
    def __init__(self, shape_type: str, title: str, color: str = THEME_COLORS['primary_green']):
        super().__init__()
        self.shape_type = shape_type
        self.title = title
        
        self.setFixedSize(90, 90)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_COLORS['bg_main']};
                border: 2px solid {THEME_COLORS['border']};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border: 2px solid {color};
                background-color: {THEME_COLORS['panel']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel()
        icon_lbl.setStyleSheet("border: none; background: transparent;")
        pix = self._create_icon(shape_type, color)
        icon_lbl.setPixmap(pix)
        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("border: none; background: transparent; font-size: 10px; color: white;")
        layout.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

    def _create_icon(self, shape_type, color):
        pix = QPixmap(40, 40)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor(color))
        p.setBrush(QColor(THEME_COLORS['bg_secondary']))
        
        if shape_type == "rect":
            p.drawRoundedRect(5, 10, 30, 20, 4, 4)
        elif shape_type == "circle":
            p.drawEllipse(5, 5, 30, 30)
        elif shape_type == "pill":
            p.drawRoundedRect(5, 10, 30, 20, 10, 10)
        elif shape_type == "diamond":
            from PySide6.QtGui import QPolygonF
            from PySide6.QtCore import QPointF
            poly = QPolygonF([
                QPointF(20, 5), QPointF(35, 20), QPointF(20, 35), QPointF(5, 20)
            ])
            p.drawPolygon(poly)
        elif shape_type == "hexagon":
            from PySide6.QtGui import QPolygonF
            from PySide6.QtCore import QPointF
            poly = QPolygonF([
                QPointF(10, 5), QPointF(30, 5), QPointF(38, 20),
                QPointF(30, 35), QPointF(10, 35), QPointF(2, 20)
            ])
            p.drawPolygon(poly)
        elif shape_type == "parallelogram":
            from PySide6.QtGui import QPolygonF
            from PySide6.QtCore import QPointF
            poly = QPolygonF([
                QPointF(10, 10), QPointF(35, 10), QPointF(30, 30), QPointF(5, 30)
            ])
            p.drawPolygon(poly)
        elif shape_type == "cloud":
            # Simple cloud drawing using circles
            p.drawEllipse(10, 15, 12, 12)
            p.drawEllipse(18, 8, 15, 15)
            p.drawEllipse(25, 15, 10, 10)
            p.drawRect(15, 18, 15, 8)
        elif shape_type == "document":
            p.drawRect(10, 5, 20, 30)
            p.drawLine(15, 10, 25, 10)
            p.drawLine(15, 15, 25, 15)
            p.drawLine(15, 20, 20, 20)
            
        p.end()
        return pix

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not hasattr(self, '_drag_start_pos'): return
        
        from PySide6.QtWidgets import QApplication
        if (event.position().toPoint() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"mind_map_template:{self.shape_type}")
        drag.setMimeData(mime_data)
        
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.position().toPoint())
        
        drag.exec(Qt.DropAction.CopyAction)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.shape_type)

class MindMapPanel(QWidget):
    shape_clicked = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15) # Increased spacing for visual breathing room
        
        info = QLabel("Drag & Drop shapes into the canvas to build your mind map.")
        info.setStyleSheet("color: #888; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        grid = QGridLayout()
        grid.setSpacing(15) # Increased grid spacing
        
        templates = [
            ("rect", "Rectangle"),
            ("circle", "Circle / Oval"),
            ("pill", "Pill"),
            ("diamond", "Decision"),
            ("hexagon", "Hexagon"),
            ("parallelogram", "Data"),
            ("cloud", "Cloud"),
            ("document", "Document")
        ]
        
        row, col = 0, 0
        for shape, title in templates:
            item = DraggableTemplate(shape, title)
            item.clicked.connect(self.shape_clicked.emit)
            # Add a minimum height so shapes are never squished
            item.setMinimumHeight(80) 
            grid.addWidget(item, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
                
        layout.addLayout(grid)
        layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
