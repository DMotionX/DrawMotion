"""
Purpose: Represents an animated drawing path in the scene.
Features: Draws a QPainterPath over time using the dash pattern technique to simulate hand-drawing.
"""
from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPen, QColor, QPainterPath, QBrush
from PySide6.QtCore import Qt, QPointF

class AnimatedStrokeItem(QGraphicsPathItem):
    def __init__(self, path: QPainterPath, stroke_color: str = "#000000", fill_color: str = None, width: int = 2):
        super().__init__()
        self.setPath(path)
        self.setFlags(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable | QGraphicsPathItem.GraphicsItemFlag.ItemIsMovable | QGraphicsPathItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self._length = path.length()
        self._progress = 2.0 # 0.0 to 1.0 (Stroke), 1.0 to 2.0 (Fill) - Default to fully visible
        self._fill_progress = 1.0 
        
        # Custom Animation Properties
        self.anim_duration = 2.0 # seconds
        self.anim_delay = 0.0 # seconds
        self.sfx_name = "None"
        self.sfx_volume = 100
        
        self.base_pen = QPen(QColor(stroke_color))
        
        # Color fill support (Disabled as per user request to keep shapes thin and outlined)
        self.fill_color = None
        self.base_pen.setWidth(2)
        self.base_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.base_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self._update_pen()

    def set_progress(self, progress: float):
        """ Set drawing progress between 0.0 and 2.0 (0-1 is stroke, 1-2 is fill) """
        self._progress = max(0.0, min(1.0, progress))
        self._fill_progress = max(0.0, min(1.0, progress - 1.0))
        
        self._update_pen()
        self._update_brush()
        
    def get_tip_position(self) -> QPointF:
        """ Returns the exact coordinate of the pen tip at the current progress """
        if self.path().isEmpty():
            return QPointF(0, 0)
        return self.path().pointAtPercent(self._progress)

    def _update_pen(self):
        if self._progress <= 0:
            self.setPen(QPen(Qt.PenStyle.NoPen))
            return
            
        pen = QPen(self.base_pen)
        if self._progress < 1.0:
            # Dash pattern trick: Draw line up to progress, then a huge gap
            current_len = self._length * self._progress
            # Minimum dash length to avoid rendering artifacts in Qt
            if current_len < 0.1:
                current_len = 0.1 
            pen.setDashPattern([current_len, self._length + 10]) # +10 to ensure it covers completely
        self.setPen(pen)

    def _update_brush(self):
        if not self.fill_color:
            self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            return
            
        if self._fill_progress <= 0:
            self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            return
            
        # Animate fill opacity
        color = QColor(self.fill_color)
        color.setAlphaF(self._fill_progress)
        self.setBrush(QBrush(color))
        
    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        
        # Draw Selection Box if selected
        if self.isSelected():
            painter.save()
            pen = QPen(QColor("#2196F3"))
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setWidth(2)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.boundingRect())
            
            # Professional resize handles (4 corners)
            painter.setBrush(QColor("#FFFFFF"))
            handle_pen = QPen(QColor("#2196F3"))
            handle_pen.setWidth(1)
            handle_pen.setCosmetic(True)
            painter.setPen(handle_pen)
            
            hs = 6 / self.scale() if self.scale() != 0 else 6
            br = self.boundingRect()
            
            # Draw square handles inside bounds
            painter.drawRect(QRectF(br.left(), br.top(), hs, hs))
            painter.drawRect(QRectF(br.right() - hs, br.top(), hs, hs))
            painter.drawRect(QRectF(br.left(), br.bottom() - hs, hs, hs))
            painter.drawRect(QRectF(br.right() - hs, br.bottom() - hs, hs, hs))
            painter.restore()

    def itemChange(self, change, value):
        return super().itemChange(change, value)
        
    def hoverMoveEvent(self, event):
        if self.isSelected():
            hs = 6 / self.scale() if self.scale() != 0 else 6
            br = self.boundingRect()
            if QRectF(br.right() - hs*2, br.bottom() - hs*2, hs*2, hs*2).contains(event.pos()):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                return
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().hoverMoveEvent(event)
        
    def mousePressEvent(self, event):
        if self.isSelected():
            hs = 6 / self.scale() if self.scale() != 0 else 6
            br = self.boundingRect()
            if QRectF(br.right() - hs*2, br.bottom() - hs*2, hs*2, hs*2).contains(event.pos()):
                self._dragging_handle = True
                self._initial_pos = event.scenePos()
                self._initial_scale = self.scale()
                event.accept()
                return
        self._dragging_handle = False
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if getattr(self, '_dragging_handle', False):
            delta = event.scenePos() - self._initial_pos
            scale_factor = 1.0 + (delta.x() / (self.boundingRect().width() * self._initial_scale))
            new_scale = max(0.1, self._initial_scale * scale_factor)
            self.setScale(new_scale)
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        if getattr(self, '_dragging_handle', False):
            self._dragging_handle = False
            if self.scene() and hasattr(self.scene(), 'parent') and hasattr(self.scene().parent(), 'items_changed'):
                self.scene().parent().items_changed.emit(self.scene().parent().user_items)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def to_dict(self):
        from core.serialization.serializer import SerializerEngine
        return {
            "type": "AnimatedStrokeItem",
            "x": self.pos().x(),
            "y": self.pos().y(),
            "scale": self.scale(),
            "rotation": self.rotation(),
            "opacity": self.opacity(),
            "anim_duration": getattr(self, "anim_duration", 2.0),
            "anim_delay": getattr(self, "anim_delay", 0.0),
            "layer_name": getattr(self, "_layer_name", "Stroke"),
            "stroke_color": self.base_pen.color().name(),
            "fill_color": self.fill_color.name() if self.fill_color else None,
            "width": self.base_pen.width(),
            "sfx_name": getattr(self, "sfx_name", "None"),
            "sfx_volume": getattr(self, "sfx_volume", 100),
            "path_elements": SerializerEngine.serialize_path(self.path())
        }
        
    @classmethod
    def from_dict(cls, data):
        from core.serialization.serializer import SerializerEngine
        path = SerializerEngine.deserialize_path(data.get("path_elements", []))
        item = cls(
            path=path,
            stroke_color=data.get("stroke_color", "#000000"),
            fill_color=data.get("fill_color", None),
            width=data.get("width", 2)
        )
        item.setPos(data.get("x", 0), data.get("y", 0))
        item.setScale(data.get("scale", 1.0))
        item.setRotation(data.get("rotation", 0))
        item.setOpacity(data.get("opacity", 1.0))
        item.anim_duration = data.get("anim_duration", 2.0)
        item.anim_delay = data.get("anim_delay", 0.0)
        item._layer_name = data.get("layer_name", "Stroke")
        item.sfx_name = data.get("sfx_name", "None")
        item.sfx_volume = data.get("sfx_volume", 100)
        return item
