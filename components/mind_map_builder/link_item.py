from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QPainter, QColor

from .models import MindMapLinkModel

class MindMapLinkItem(QGraphicsObject):
    def __init__(self, model: MindMapLinkModel, source_node, target_node, canvas_workspace=None):
        super().__init__()
        self.model = model
        self.source_node = source_node
        self.target_node = target_node
        self.canvas_workspace = canvas_workspace
        
        self.setZValue(-1) # Behind nodes
        self.progress = 1.0
        
        # Connect to node movements
        self.source_node.moved.connect(self.update_position)
        self.target_node.moved.connect(self.update_position)
        
        self.update_position()

    def update_position(self, _=None):
        self.prepareGeometryChange()
        self.update()

    def boundingRect(self) -> QRectF:
        if not self.source_node or not self.target_node:
            return QRectF()
            
        p1 = self.source_node.scenePos() + QPointF(self.source_node.model.width/2, self.source_node.model.height/2)
        p2 = self.target_node.scenePos() + QPointF(self.target_node.model.width/2, self.target_node.model.height/2)
        
        return QRectF(p1, p2).normalized().adjusted(-10, -10, 10, 10)

    def paint(self, painter: QPainter, option, widget=None):
        if not self.source_node or not self.target_node or self.progress <= 0:
            return
            
        # Get center points
        p1 = self.source_node.scenePos() + QPointF(self.source_node.model.width/2, self.source_node.model.height/2)
        p2 = self.target_node.scenePos() + QPointF(self.target_node.model.width/2, self.target_node.model.height/2)
        
        # Map to local coordinates
        p1 = self.mapFromScene(p1)
        p2 = self.mapFromScene(p2)
        
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(p1)
        # Control points for a smooth cubic bezier
        dx = abs(p2.x() - p1.x()) / 2.0
        c1 = QPointF(p1.x() + dx, p1.y())
        c2 = QPointF(p2.x() - dx, p2.y())
        path.cubicTo(c1, c2, p2)
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(self.model.color))
        pen.setWidthF(self.model.thickness)
        
        # Animate drawing using dash pattern
        dash_len = path.length() / max(1.0, pen.widthF())
        draw_len = dash_len * self.progress
        pen.setDashPattern([draw_len, dash_len])
        painter.setPen(pen)
        
        painter.drawPath(path)

    # For animation logic
    def set_progress(self, progress: float):
        self.progress = progress
        self.update()
        
    def get_tip_position(self) -> QPointF:
        p1 = self.source_node.scenePos() + QPointF(self.source_node.model.width/2, self.source_node.model.height/2)
        p2 = self.target_node.scenePos() + QPointF(self.target_node.model.width/2, self.target_node.model.height/2)
        
        p1 = self.mapFromScene(p1)
        p2 = self.mapFromScene(p2)
        
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(p1)
        dx = abs(p2.x() - p1.x()) / 2.0
        c1 = QPointF(p1.x() + dx, p1.y())
        c2 = QPointF(p2.x() - dx, p2.y())
        path.cubicTo(c1, c2, p2)
        
        # For tip position in global coordinates, we need to map back to scene if necessary, 
        # but animator engine treats tip_position as local relative to the item itself.
        return path.pointAtPercent(self.progress)
