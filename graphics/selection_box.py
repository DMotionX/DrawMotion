from PySide6.QtWidgets import QGraphicsObject
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

class SelectionBox(QGraphicsObject):
    def __init__(self, target_item, parent=None):
        super().__init__(parent)
        self.target = target_item
        self.setZValue(1000)
        self.setFlags(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable | QGraphicsObject.GraphicsItemFlag.ItemIsMovable)
        
        # When target moves or scales, this should update
        self.target.xChanged.connect(self.update_geometry) if hasattr(self.target, 'xChanged') else None
        
        self.rect = self.target.boundingRect()
        self.handle_size = 10
        self._dragging_handle = None
        
        self.setAcceptHoverEvents(True)
        
    def boundingRect(self):
        # Slightly larger than target
        return self.rect.adjusted(-self.handle_size, -self.handle_size, self.handle_size, self.handle_size)
        
    def update_geometry(self):
        if self.target.scene():
            self.setPos(self.target.scenePos())
            self.setRotation(self.target.rotation())
            self.setScale(self.target.scale())
            self.update()
            
    def paint(self, painter, option, widget=None):
        # Draw dashed outline
        pen = QPen(QColor("#4CAF50"))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(2)
        # Prevent pen width scaling
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect)
        
        # Draw handles
        painter.setBrush(QBrush(QColor("#4CAF50")))
        painter.setPen(Qt.PenStyle.NoPen)
        hs = self.handle_size / self.scale() if self.scale() != 0 else self.handle_size
        
        # Corners
        corners = [
            self.rect.topLeft(),
            self.rect.topRight(),
            self.rect.bottomLeft(),
            self.rect.bottomRight()
        ]
        
        for p in corners:
            painter.drawRect(QRectF(p.x() - hs/2, p.y() - hs/2, hs, hs))
            
    def hoverMoveEvent(self, event):
        pos = event.pos()
        hs = self.handle_size / self.scale() if self.scale() != 0 else self.handle_size
        
        # Check if over a corner
        if QRectF(self.rect.bottomRight().x() - hs, self.rect.bottomRight().y() - hs, hs*2, hs*2).contains(pos):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
        super().hoverMoveEvent(event)
        
    def mousePressEvent(self, event):
        pos = event.pos()
        hs = self.handle_size / self.scale() if self.scale() != 0 else self.handle_size
        if QRectF(self.rect.bottomRight().x() - hs, self.rect.bottomRight().y() - hs, hs*2, hs*2).contains(pos):
            self._dragging_handle = 'br'
            self._initial_pos = event.scenePos()
            self._initial_scale = self.target.scale()
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        if self._dragging_handle == 'br':
            delta = event.scenePos() - self._initial_pos
            # Simple uniform scaling based on x movement
            scale_factor = 1.0 + (delta.x() / (self.rect.width() * self._initial_scale))
            new_scale = max(0.1, self._initial_scale * scale_factor)
            
            self.target.setScale(new_scale)
            self.setScale(new_scale)
            
            # Notify canvas to update Inspector
            if hasattr(self.scene(), 'parent') and hasattr(self.scene().parent(), 'item_modified'):
                pass
            event.accept()
        else:
            super().mouseMoveEvent(event)
            # Sync target pos
            self.target.setPos(self.scenePos())
            
    def mouseReleaseEvent(self, event):
        if self._dragging_handle:
            self._dragging_handle = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
