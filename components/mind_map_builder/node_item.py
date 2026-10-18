from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsProxyWidget
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QPainterPath, QLinearGradient

from .models import MindMapNodeModel
from components.write_to_image.text_editor import TextEditorWidget

class NodeHandle(QGraphicsRectItem):
    def __init__(self, parent=None, position="bottom-right"):
        super().__init__(-4, -4, 8, 8, parent)
        self.setBrush(QBrush(QColor("#2563EB")))
        self.setPen(Qt.PenStyle.NoPen)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.position_type = position
        self.hide()
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        parent = self.parentItem()
        if hasattr(parent, 'model') and hasattr(parent.model, 'width'):
            self._aspect_ratio = parent.model.width / max(1.0, parent.model.height)
        else:
            self._aspect_ratio = None

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.parentItem():
            parent = self.parentItem()
            
            # Prevent infinite recursion if the parent is updating programmatically
            if getattr(parent, '_is_updating', False):
                return super().itemChange(change, value)
                
            new_pos = value
            new_pos.setX(max(new_pos.x(), 20.0))
            new_pos.setY(max(new_pos.y(), 20.0))
            
            if hasattr(self, '_aspect_ratio') and self._aspect_ratio:
                # Maintain aspect ratio based on width drag
                new_y = new_pos.x() / self._aspect_ratio
                new_pos.setY(new_y)
                
            if hasattr(parent, 'model'):
                if hasattr(parent.model, 'width'): # For mind map nodes AND Write-to-Image
                    parent.model.width = new_pos.x()
                    parent.model.height = new_pos.y()
                    
            if hasattr(parent, 'update_geometry_and_cache'):
                parent.update_geometry_and_cache()
            elif hasattr(parent, 'prepareGeometryChange'):
                parent.prepareGeometryChange()
            parent.update()
            
            return new_pos
            
        return super().itemChange(change, value)

class PortHandle(QGraphicsEllipseItem):
    def __init__(self, parent=None):
        super().__init__(-6, -6, 12, 12, parent)
        self.setBrush(QBrush(QColor("#10B981")))
        self.setPen(QPen(QColor("#047857"), 1))
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.hide()
        
        self.drag_line = None
        self.start_scene_pos = None

    def mousePressEvent(self, event):
        from PySide6.QtWidgets import QGraphicsPathItem
        self.start_scene_pos = self.mapToScene(event.pos())
        self.drag_line = QGraphicsPathItem()
        pen = QPen(QColor("#10B981"))
        pen.setWidthF(2.0)
        pen.setStyle(Qt.PenStyle.DashLine)
        self.drag_line.setPen(pen)
        self.scene().addItem(self.drag_line)
        event.accept()

    def mouseMoveEvent(self, event):
        if not self.drag_line: return
        current_scene_pos = self.mapToScene(event.pos())
        
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(self.start_scene_pos)
        dx = abs(current_scene_pos.x() - self.start_scene_pos.x()) / 2.0
        c1 = QPointF(self.start_scene_pos.x() + dx, self.start_scene_pos.y())
        c2 = QPointF(current_scene_pos.x() - dx, current_scene_pos.y())
        path.cubicTo(c1, c2, current_scene_pos)
        
        self.drag_line.setPath(path)
        event.accept()

    def mouseReleaseEvent(self, event):
        if self.drag_line:
            self.scene().removeItem(self.drag_line)
            self.drag_line = None
            
        current_scene_pos = self.mapToScene(event.pos())
        items = self.scene().items(current_scene_pos)
        
        target_node = None
        for item in items:
            if isinstance(item, MindMapNodeItem) and item != self.parentItem():
                target_node = item
                break
                
        if target_node:
            source_node = self.parentItem()
            workspace = source_node.canvas_workspace
            if workspace:
                # Create Link Model
                from components.mind_map_builder.models import MindMapLinkModel
                from components.mind_map_builder.link_item import MindMapLinkItem
                import uuid
                
                link_model = MindMapLinkModel(
                    id=f"link_{uuid.uuid4().hex[:8]}",
                    name="Link",
                    source_node_id=source_node.model.id,
                    target_node_id=target_node.model.id
                )
                link_item = MindMapLinkItem(link_model, source_node, target_node, workspace)
                
                # Add to workspace
                link_item.setParentItem(source_node.parentItem()) # artboard
                workspace.scene.addItem(link_item)
                workspace.user_items.append(link_item)
                
                # Default anim properties
                link_item.anim_duration = 1.0
                link_item.layer_name = "Link"
                link_item.draw_order = len(workspace.user_items)
                
                workspace.distribute_global_time()
                workspace.items_changed.emit(workspace.get_current_scene_items())
                
        event.accept()

class MindMapNodeItem(QGraphicsObject):
    moved = Signal(object) # Emits self when moved
    
    def __init__(self, model: MindMapNodeModel, canvas_workspace=None):
        super().__init__()
        self.model = model
        self.canvas_workspace = canvas_workspace
        
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True) 
        self.setPos(self.model.pos_x, self.model.pos_y)
        
        self.progress = 1.0 
        self._is_updating = False
        
        self.resize_handle = NodeHandle(self, "bottom-right")
        self.port_top = PortHandle(self)
        self.port_bottom = PortHandle(self)
        self.port_left = PortHandle(self)
        self.port_right = PortHandle(self)
        
        self._cached_path = QPainterPath()
        self._cached_dash_len = 0.0
        self._cached_text_rect = QRectF()
        
        self.update_geometry_and_cache()
        
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)
        
    def update_geometry_and_cache(self):
        self._is_updating = True
        self.prepareGeometryChange()
        w, h = self.model.width, self.model.height
        
        path = QPainterPath()
        text_rect = QRectF(0, 0, w, h)
        
        if self.model.shape_type == "rect":
            path.addRoundedRect(0, 0, w, h, 8, 8)
            text_rect = QRectF(8, 8, w-16, h-16)
        elif self.model.shape_type in ["circle", "ellipse"]:
            path.addEllipse(0, 0, w, h)
            import math
            ix = w * (1 - 1/math.sqrt(2)) / 2
            iy = h * (1 - 1/math.sqrt(2)) / 2
            iw = w / math.sqrt(2)
            ih = h / math.sqrt(2)
            text_rect = QRectF(ix, iy, iw, ih)
        elif self.model.shape_type == "pill":
            path.addRoundedRect(0, 0, w, h, h/2, h/2)
            text_rect = QRectF(h/2, 0, w-h, h)
        elif self.model.shape_type == "diamond":
            from PySide6.QtGui import QPolygonF
            poly = QPolygonF([QPointF(w/2, 0), QPointF(w, h/2), QPointF(w/2, h), QPointF(0, h/2)])
            path.addPolygon(poly)
            text_rect = QRectF(w/4, h/4, w/2, h/2)
        elif self.model.shape_type == "hexagon":
            from PySide6.QtGui import QPolygonF
            dw = w * 0.2
            poly = QPolygonF([QPointF(dw, 0), QPointF(w-dw, 0), QPointF(w, h/2), QPointF(w-dw, h), QPointF(dw, h), QPointF(0, h/2)])
            path.addPolygon(poly)
            text_rect = QRectF(dw, 0, w - 2*dw, h)
        elif self.model.shape_type == "parallelogram":
            from PySide6.QtGui import QPolygonF
            dw = w * 0.2
            poly = QPolygonF([QPointF(dw, 0), QPointF(w, 0), QPointF(w-dw, h), QPointF(0, h)])
            path.addPolygon(poly)
            text_rect = QRectF(dw, 0, w - 2*dw, h)
        elif self.model.shape_type == "cloud":
            path.addEllipse(w*0.1, h*0.2, w*0.4, h*0.4)
            path.addEllipse(w*0.3, h*0.1, w*0.5, h*0.5)
            path.addEllipse(w*0.6, h*0.3, w*0.3, h*0.4)
            path.addRect(w*0.2, h*0.4, w*0.6, h*0.4)
            text_rect = QRectF(w*0.2, h*0.3, w*0.6, h*0.5)
        elif self.model.shape_type == "document":
            path.addRect(0, 0, w, h)
            text_rect = QRectF(10, 10, w-20, h-20)
        else:
            path.addRoundedRect(0, 0, w, h, 8, 8)
            text_rect = QRectF(8, 8, w-16, h-16)
            
        self._cached_path = path
        self._cached_text_rect = text_rect
        
        pen = QPen(QColor(self.model.stroke_color))
        pen.setWidthF(2.0)
        self._cached_dash_len = path.length() / max(1.0, pen.widthF())
        
        if self.resize_handle.pos() != QPointF(w, h):
            self.resize_handle.setPos(w, h)
            
        self.port_top.setPos(w / 2, 0)
        self.port_bottom.setPos(w / 2, h)
        self.port_left.setPos(0, h / 2)
        self.port_right.setPos(w, h / 2)
        
        self._is_updating = False

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.model.width, self.model.height)
        
    def hoverEnterEvent(self, event):
        self.port_top.show()
        self.port_bottom.show()
        self.port_left.show()
        self.port_right.show()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.port_top.hide()
        self.port_bottom.hide()
        self.port_left.hide()
        self.port_right.hide()
        super().hoverLeaveEvent(event)
        
    def paint(self, painter: QPainter, option, widget=None):
        if self.progress <= 0: return
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.model.width, self.model.height
        
        painter.save()
        pen = QPen(QColor(self.model.stroke_color))
        pen.setWidthF(2.0)
        
        dash_len = self._cached_dash_len
        draw_len = dash_len * self.progress
        pen.setDashPattern([draw_len, dash_len])
        painter.setPen(pen)
        
        fill_alpha = min(255, max(0, int((self.progress - 0.5) * 2.0 * 255)))
        gradient = QLinearGradient(0, 0, 0, h)
        base_c = QColor(self.model.fill_color)
        if base_c.name() == "#ffffff":
            base_c = QColor("#F8FAFC")
            
        c1 = base_c.lighter(105)
        c2 = base_c.darker(105)
        c1.setAlpha(fill_alpha)
        c2.setAlpha(fill_alpha)
        gradient.setColorAt(0.0, c1)
        gradient.setColorAt(1.0, c2)
        painter.setBrush(QBrush(gradient))
        
        painter.drawPath(self._cached_path)
        
        if self.model.shape_type == "document" and self.progress > 0.5:
            painter.setPen(QPen(QColor(self.model.stroke_color), 1))
            painter.drawLine(w*0.3, h*0.2, w*0.7, h*0.2)
            painter.drawLine(w*0.3, h*0.4, w*0.7, h*0.4)
            painter.drawLine(w*0.3, h*0.6, w*0.5, h*0.6)
            
        if fill_alpha > 0:
            text_color = QColor(self.model.text_color)
            text_color.setAlpha(fill_alpha)
            painter.setPen(text_color)
            font = painter.font()
            
            base_width = 120.0
            scale_factor = self.model.width / base_width
            dynamic_font_size = int(self.model.font_size * scale_factor)
            font.setPointSize(max(4, dynamic_font_size))
            
            painter.setFont(font)
            painter.drawText(self._cached_text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.model.text)
            
        painter.restore()

        if self.isSelected():
            painter.setPen(QPen(QColor("#2563EB"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(-4, -4, w + 8, h + 8)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.moved.emit(self)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self.isSelected():
                self.resize_handle.show()
            else:
                self.resize_handle.hide()
        return super().itemChange(change, value)
        
    def mouseDoubleClickEvent(self, event):
        if self.canvas_workspace:
            from components.write_to_image.text_editor import TextEditorWidget
            view = self.canvas_workspace.view
            scene_pos = self.scenePos()
            view_pos = view.mapFromScene(scene_pos)
            
            from components.write_to_image.models import WriteToImageModel
            dummy_model = WriteToImageModel(
                id=self.model.id, name="temp",
                text=self.model.text,
                font_family="Arial", font_size=self.model.font_size,
                color=self.model.text_color, pos_x=scene_pos.x(), pos_y=scene_pos.y()
            )
            
            self.editor = TextEditorWidget(view_pos.x(), view_pos.y(), existing_model=dummy_model, parent=view)
            self.editor.editing_finished.connect(self._on_text_edited)
            self.editor.show()
            self.editor.setFocus()
            
    def _on_text_edited(self, updated_model):
        if updated_model:
            self.model.text = updated_model.text
            self.update()
            
    def set_progress(self, progress: float):
        self.progress = progress
        
        shadow = self.graphicsEffect()
        if shadow:
            if self.progress >= 0.99:
                shadow.setEnabled(True)
            else:
                shadow.setEnabled(False)
                
        self.update()
        
    def get_tip_position(self) -> QPointF:
        if self._cached_path.isEmpty():
            x = self.model.width * self.progress
            return QPointF(x, self.model.height / 2)
        # Perfectly trace the edges of the shape for the drawing hand
        return self._cached_path.pointAtPercent(max(0.0, min(1.0, self.progress)))
