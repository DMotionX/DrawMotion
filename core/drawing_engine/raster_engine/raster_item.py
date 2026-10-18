from PySide6.QtWidgets import QGraphicsObject
from PySide6.QtCore import Qt, QRectF, Property, QPointF, QSize, Signal
from PySide6.QtGui import QPainter, QPixmap
import math

def ease_in_out_cubic(t):
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4 * t * t * t
    return 1 - math.pow(-2 * t + 2, 3) / 2

class AnimatedRasterItem(QGraphicsObject):
    """
    Independent Raster Engine for PNG/JPG images (Phase 2).
    Zero-lag architecture: Uses native clipping instead of alpha masking.
    Generates a single-sweep plan for the hand without heavy mathematical algorithms.
    """
    plan_started = Signal()
    plan_ready = Signal()

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._pixmap         = pixmap
        self._progress       = 1.0
        self.anim_duration   = 8.0
        self.anim_delay      = 0.0
        self.layer_name      = "Image"
        self.drawing_style   = "Left-to-Right Sweep"
        self.anim_type       = "Draw"
        self.anim_dir        = "From Left"
        self.anim_easing     = "Linear"
        self.image_path      = ""
        self.sfx_name        = "None"
        self.sfx_volume      = 100

        # Limit to 1080 internally to save memory
        max_res = 1080.0
        w, h = self._pixmap.width(), self._pixmap.height()
        if w > max_res or h > max_res:
            scale_factor = min(max_res / w, max_res / h)
            new_size = QSize(int(w * scale_factor), int(h * scale_factor))
            self._pixmap = self._pixmap.scaled(
                new_size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            w, h = self._pixmap.width(), self._pixmap.height()

        # Visually fit large images in the canvas
        max_size = 400.0
        if w > max_size or h > max_size:
            self.setScale(min(max_size / w, max_size / h))

        self.setFlags(
            QGraphicsObject.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsObject.GraphicsItemFlag.ItemIsMovable |
            QGraphicsObject.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self._timed_segments = []
        
        # Build plan instantly without background threads
        self.update_plan()

    def boundingRect(self):
        return QRectF(self._pixmap.rect())

    def shape(self):
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def update_plan(self):
        """
        Creates a lightning-fast single-sweep plan.
        No OpenCV, no contour mapping. 100% Zero-Lag.
        """
        self.plan_started.emit()
        
        w = float(self._pixmap.width())
        h = float(self._pixmap.height())
        
        segment = {
            "points": [QPointF(0, h/2), QPointF(w, h/2)],
            "duration": self.anim_duration,
            "start_time": 0.0,
            "end_time": self.anim_duration,
            "width": h,
            "active_duration": self.anim_duration,
            "length": w
        }
        
        self._timed_segments = [segment]
        self.plan_ready.emit()

    def get_animation_plan(self):
        return self._timed_segments

    def _get_progress(self):
        return self._progress

    def _set_progress(self, val):
        val = max(0.0, min(1.0, val))
        if self._progress != val:
            self._progress = val
            # Easing applied locally
            self._eased_progress = ease_in_out_cubic(val)
            self.update()

    progress = Property(float, _get_progress, _set_progress)

    def set_progress(self, val):
        self.progress = val

    def set_anim_duration(self, val):
        self.anim_duration = val
        self.update_plan()

    def paint(self, painter, option, widget=None):
        """
        Ultra-fast rendering.
        Instead of composing alpha buffers frame-by-frame, we simply draw 
        a clipped portion of the image based on progress.
        """
        rect = self.boundingRect()
        
        if self._progress <= 0.0:
            return
            
        if self._progress >= 1.0:
            painter.drawPixmap(rect.toRect(), self._pixmap)
            # Draw selection border
            if self.isSelected():
                painter.setPen(Qt.GlobalColor.blue)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect)
            return

        # Native Hardware Clipping (0 Lag)
        # Assuming Left-to-Right sweep
        clip_width = rect.width() * self._eased_progress
        clip_rect = QRectF(rect.x(), rect.y(), clip_width, rect.height())
        
        painter.save()
        painter.setClipRect(clip_rect)
        painter.drawPixmap(rect.toRect(), self._pixmap)
        painter.restore()

        if self.isSelected():
            painter.setPen(Qt.GlobalColor.blue)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)

    def to_dict(self):
        return {
            "type": "AnimatedRasterItem",
            "x": self.pos().x(),
            "y": self.pos().y(),
            "rotation": self.rotation(),
            "scale": self.scale(),
            "opacity": self.opacity(),
            "layer_name": self.layer_name,
            "anim_duration": self.anim_duration,
            "anim_delay": self.anim_delay,
            "drawing_style": self.drawing_style,
            "anim_type": self.anim_type,
            "anim_dir": self.anim_dir,
            "anim_easing": self.anim_easing,
            "sfx_name": getattr(self, "sfx_name", "None"),
            "sfx_volume": getattr(self, "sfx_volume", 100),
            "image_path": getattr(self, 'image_path', "")
        }

    @classmethod
    def from_dict(cls, data):
        image_path = data.get('image_path', "")
        pixmap = QPixmap(image_path) if image_path else QPixmap()
        item = cls(pixmap)
        item.image_path = image_path
        
        item.setPos(data.get('x', 0), data.get('y', 0))
        item.setRotation(data.get('rotation', 0))
        item.setScale(data.get('scale', 1.0))
        item.setOpacity(data.get('opacity', 1.0))
        item.layer_name = data.get('layer_name', "Image")
        item.anim_duration = data.get('anim_duration', 8.0)
        item.anim_delay = data.get('anim_delay', 0.0)
        item.drawing_style = data.get('drawing_style', "Left-to-Right Sweep")
        item.anim_type = data.get('anim_type', "Draw")
        item.anim_dir = data.get('anim_dir', "From Left")
        item.anim_easing = data.get('anim_easing', "Linear")
        item.sfx_name = data.get('sfx_name', "None")
        item.sfx_volume = data.get('sfx_volume', 100)
        
        item.update_plan()
        return item
