import os
import math
import re
from PySide6.QtWidgets import QGraphicsObject, QGraphicsItem
from PySide6.QtCore import Qt, QPointF, QRectF, QSize, QThread, QRunnable, QThreadPool, Signal, QObject
from PySide6.QtGui import QPainter, QPixmap, QImage, QPen, QColor, QPainterPath
import cv2
import numpy as np

from .models import WriteToImageModel
from .text_editor import TextEditorWidget
from .time_map_generator import generate_time_map

class WriteToImageGraphicsItem(QGraphicsObject):
    def __init__(self, model, canvas_workspace=None):
        super().__init__()
        # CRITICAL FIX: Trick the animator_engine to bypass the 1000px width scaling bug.
        # But we MUST still include "AnimatedImageItem" so it is treated as an image
        # with max_progress=1.0 and opacity=1.0. 
        self.__class__.__name__ = "WriteToAnimatedImageItem"
        
        self.model = model
        self.canvas_workspace = canvas_workspace
        self.model.item_type = "write_to_image"
        
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        
        # Core Position and Scale (Ensures properties match model)
        self.setPos(self.model.pos_x, self.model.pos_y)
        self.setScale(getattr(self.model, 'scale_w', 1.0))
        
        # Animation properties
        self.progress = 1.0
        
        self.is_rtl = self._check_if_rtl(self.model.text)
        self.direction = Qt.LayoutDirection.RightToLeft if self.is_rtl else Qt.LayoutDirection.LeftToRight
        
        # Fast-Travel for English (0.05s per char instead of 0.10s)
        multiplier = 0.10 if self.is_rtl else 0.05
        default_dur = max(1.5, len(getattr(self.model, 'text', '')) * multiplier)
        
        self._anim_duration = getattr(self.model, 'duration', default_dur)
        self.model.duration = self._anim_duration
        self.drawing_style = "Solid Reveal"
        self._anim_delay = 0.0
        self._layer_name = "default"
        print(f"[GraphicsItem LOG] Init. Text: '{self.model.text[:10]}...', Duration set to: {self._anim_duration}s (Model Duration: {getattr(self.model, 'duration', None)})")
        
        # Animation properties
        self._last_drawn_progress = -1.0
        
        self._load_image()

    def _check_if_rtl(self, text: str) -> bool:
        if not text: return False
        
        # [Phase 8 FIX]: Smart Dominant Language Detection (Zero-Risk)
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        # If Arabic is strictly greater than English, treat as RTL.
        # Otherwise, treat as LTR (Default for English or numbers/symbols).
        return arabic_chars > english_chars

    def _load_image(self):
        if self.model.image_path and os.path.exists(self.model.image_path):
            # 1. Load the clean base text for accurate time map skeletonization
            self._original_image = QImage(self.model.image_path)
            
            # 2. Load the display image (with effects) if available
            display_path = self.model.image_path.replace(".png", "_display.png")
            if os.path.exists(display_path):
                self._pixmap = QPixmap(display_path)
            else:
                self._pixmap = QPixmap(self.model.image_path)
            
            self.is_rtl = self._check_if_rtl(self.model.text)
            self.direction = Qt.LayoutDirection.RightToLeft if self.is_rtl else Qt.LayoutDirection.LeftToRight
            
            # Use DevicePixelRatio to maintain crispness at 5x scale WITHOUT using self.setScale(0.2)
            self._pixmap.setDevicePixelRatio(5.0)
            
            # Load char map
            char_map = []
            map_path = self.model.image_path.replace(".png", "_charmap.json")
            if os.path.exists(map_path):
                import json
                try:
                    with open(map_path, "r", encoding="utf-8") as f:
                        char_map = json.load(f)
                except Exception:
                    pass
                    
            # Generate Time Map for smooth human-like reveal using the clean base image!
            self._time_map = generate_time_map(self._original_image, self.is_rtl, char_map)
            self._generate_trajectory()
            
            # Auto-upgrade old models that had scale_w = 0.2 due to previous hack
            if getattr(self.model, 'scale_w', 1.0) == 0.2:
                self.model.scale_w = 1.0
                self.model.scale_h = 1.0
                self.setScale(1.0)
                
            if not hasattr(self.model, 'scale_w') or self.model.scale_w <= 0.0:
                self.model.scale_w = 1.0
                self.model.scale_h = 1.0
                self.setScale(1.0)
                
            self.prepareGeometryChange()
            self.update()
        else:
            self._pixmap = None

    def _generate_trajectory(self):
        self._trajectory = []
        if not hasattr(self, '_time_map') or self._time_map is None:
            return
            
        for t in range(256):
            # Find all pixels that are revealed at exactly this time t
            y_coords, x_coords = np.where(self._time_map == t)
            if len(y_coords) > 0:
                cx, cy = np.mean(x_coords), np.mean(y_coords)
                self._trajectory.append(QPointF(cx, cy))
            else:
                if self._trajectory:
                    self._trajectory.append(self._trajectory[-1])
                else:
                    self._trajectory.append(self.boundingRect().center())

    @property
    def anim_duration(self) -> float:
        return self._anim_duration

    @anim_duration.setter
    def anim_duration(self, val: float):
        self.set_anim_duration(val)

    @property
    def anim_delay(self) -> float:
        return getattr(self.model, 'delay', 0.0)

    @anim_delay.setter
    def anim_delay(self, val: float):
        self.model.delay = val

    def set_anim_duration(self, duration: float):
        print(f"[GraphicsItem LOG] set_anim_duration called with: {duration}s")
        if self._anim_duration != duration:
            self._anim_duration = duration
            self.model.duration = duration
            if self.model.image_path:
                # No plan building needed with dynamic clipping
                pass
        self.update()

    def boundingRect(self) -> QRectF:
        if not getattr(self, '_pixmap', None): return QRectF()
        dpr = self._pixmap.devicePixelRatio()
        return QRectF(0, 0, self._pixmap.width() / dpr, self._pixmap.height() / dpr)

    def set_progress(self, progress: float):
        self.progress = min(max(progress, 0.0), 1.0)
        self.update()

    def _get_effective_progress(self):
        return self.progress

    def _get_exact_target(self):
        if not hasattr(self, '_trajectory') or not self._trajectory or self.progress <= 0:
            return self.boundingRect().center()
            
        idx = int(self.progress * 255)
        idx = min(max(idx, 0), 255)
        
        dpr = self._pixmap.devicePixelRatio()
        pt = self._trajectory[idx]
        return QPointF(pt.x() / dpr, pt.y() / dpr)

    def get_tip_position(self) -> QPointF:
        return self._get_exact_target()

    # ── Properties for Animator Engine ───────────────────────────────────────

    @property
    def anim_duration(self):
        return getattr(self, '_anim_duration', 1.0)

    @anim_duration.setter
    def anim_duration(self, v):
        self._anim_duration = v
        self.model.duration = v
        self.update()

    @property
    def anim_delay(self):
        return getattr(self, '_anim_delay', 0.0)

    @anim_delay.setter
    def anim_delay(self, v):
        self._anim_delay = v

    @property
    def layer_name(self):
        return getattr(self, '_layer_name', "default")

    @layer_name.setter
    def layer_name(self, v):
        self._layer_name = v
        
    @property
    def sfx_name(self):
        return getattr(self.model, 'sfx_name', 'None')
        
    @sfx_name.setter
    def sfx_name(self, v):
        self.model.sfx_name = v
        
    @property
    def sfx_volume(self):
        return getattr(self.model, 'sfx_volume', 100)
        
    @sfx_volume.setter
    def sfx_volume(self, v):
        self.model.sfx_volume = v

    # ─────────────────────────────────────────────────────────────────────────

    def paint(self, painter: QPainter, option, widget=None):
        if not getattr(self, '_pixmap', None) or self._pixmap.isNull():
            return
            
        if self.isSelected():
            self._paint_selection(painter)
            
        p = self.progress
        rect = self.boundingRect()
        
        if p <= 0:
            return
            
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        if p >= 1.0 or getattr(self, '_time_map', None) is None:
            painter.drawPixmap(0, 0, self._pixmap)
            return
            
        # Fast Dynamic Time-Map Mask (Human-like text reveal, 0% CPU lag)
        threshold_val = int(p * 255)
        # mask = 255 where time_map <= threshold_val
        _, mask = cv2.threshold(self._time_map, threshold_val, 255, cv2.THRESH_BINARY_INV)
        
        h, w = mask.shape
        mask_bytes = mask.tobytes()
        mask_qimage = QImage(mask_bytes, w, h, w, QImage.Format_Alpha8)
        mask_qimage.setDevicePixelRatio(self._pixmap.devicePixelRatio())
        
        temp_img = QImage(self._pixmap.size(), QImage.Format_ARGB32_Premultiplied)
        temp_img.fill(Qt.transparent)
        temp_img.setDevicePixelRatio(self._pixmap.devicePixelRatio())
        
        p2 = QPainter(temp_img)
        p2.setRenderHint(QPainter.RenderHint.Antialiasing)
        p2.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        # Draw the display image (with effects)
        p2.drawImage(0, 0, self._pixmap.toImage())
        p2.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        p2.drawImage(0, 0, mask_qimage)
        p2.end()
        
        painter.drawImage(0, 0, temp_img)

    # ── Interactive Resizing ──────────────────────────────────────────────────

    def _paint_selection(self, painter):
        pen = QPen(QColor("#2196F3"))
        pen.setStyle(Qt.PenStyle.SolidLine)
        pen.setWidth(2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.boundingRect())

        painter.setBrush(QColor("#FFFFFF"))
        h_pen = QPen(QColor("#2196F3"))
        h_pen.setWidth(1)
        h_pen.setCosmetic(True)
        painter.setPen(h_pen)
        
        hs = 8 / self.scale() if self.scale() != 0 else 8
        br = self.boundingRect()
        mid_x = (br.left() + br.right()) / 2.0
        mid_y = (br.top() + br.bottom()) / 2.0
        handles = [
            (br.left(), br.top()),       # TL
            (mid_x, br.top()),           # TC
            (br.right(), br.top()),      # TR
            (br.right(), mid_y),         # RC
            (br.right(), br.bottom()),   # BR
            (mid_x, br.bottom()),        # BC
            (br.left(), br.bottom()),    # BL
            (br.left(), mid_y)           # LC
        ]
        for cx, cy in handles:
            painter.drawRect(QRectF(cx - hs/2, cy - hs/2, hs, hs))

    def shape(self):
        path = QPainterPath()
        s = self.scale() if self.scale() > 0 else 1.0
        pad = 14.0 / s
        path.addRect(self.boundingRect().adjusted(-pad, -pad, pad, pad))
        return path

    def hoverMoveEvent(self, event):
        pos = event.pos()
        br = self.boundingRect()
        s = self.scale() if self.scale() > 0 else 1.0
        
        # Responsive edge and corner margins
        edge_margin = 12.0 / s
        corner_reach = 24.0 / s
        
        min_dim = min(br.width(), br.height())
        if min_dim > 0:
            edge_margin = min(edge_margin, min_dim * 0.35)
            corner_reach = min(corner_reach, min_dim * 0.45)
            
        x, y = pos.x(), pos.y()
        left, top, right, bottom = br.left(), br.top(), br.right(), br.bottom()
        
        # Check boundary proximity (Resize Zone)
        near_left = abs(x - left) <= edge_margin
        near_right = abs(x - right) <= edge_margin
        near_top = abs(y - top) <= edge_margin
        near_bottom = abs(y - bottom) <= edge_margin
        
        outside_left = (x < left)
        outside_right = (x > right)
        outside_top = (y < top)
        outside_bottom = (y > bottom)
        
        is_on_edge = (near_left or near_right or near_top or near_bottom or
                      outside_left or outside_right or outside_top or outside_bottom)

        if is_on_edge:
            # 1. Corners (TL, TR, BL, BR) take top priority
            is_top_corner = (y <= top + corner_reach)
            is_bottom_corner = (y >= bottom - corner_reach)
            is_left_corner = (x <= left + corner_reach)
            is_right_corner = (x >= right - corner_reach)

            if (is_left_corner and is_top_corner) or (near_left and is_top_corner) or (near_top and is_left_corner):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                self._hover_handle = "TL"
            elif (is_right_corner and is_bottom_corner) or (near_right and is_bottom_corner) or (near_bottom and is_right_corner):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                self._hover_handle = "BR"
            elif (is_right_corner and is_top_corner) or (near_right and is_top_corner) or (near_top and is_right_corner):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                self._hover_handle = "TR"
            elif (is_left_corner and is_bottom_corner) or (near_left and is_bottom_corner) or (near_bottom and is_left_corner):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
                self._hover_handle = "BL"
            # 2. Side edges (Top, Bottom, Left, Right)
            elif near_top or (outside_top and left <= x <= right):
                self.setCursor(Qt.CursorShape.SizeVerCursor)
                self._hover_handle = "TC"
            elif near_bottom or (outside_bottom and left <= x <= right):
                self.setCursor(Qt.CursorShape.SizeVerCursor)
                self._hover_handle = "BC"
            elif near_left or (outside_left and top <= y <= bottom):
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                self._hover_handle = "LC"
            elif near_right or (outside_right and top <= y <= bottom):
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                self._hover_handle = "RC"
            else:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
                self._hover_handle = None
        else:
            # Deep inside image -> Move/Grab zone ("المقبض")
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self._hover_handle = None

        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._hover_handle = None
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        handle = getattr(self, "_hover_handle", None)
        if handle and event.button() == Qt.MouseButton.LeftButton:
            self._is_resizing = True
            self._active_handle = handle
            self._resize_start_pos = event.scenePos()
            self._resize_start_scale = self.scale()
            
            br = self.boundingRect()
            mid_x = (br.left() + br.right()) / 2.0
            mid_y = (br.top() + br.bottom()) / 2.0
            
            if handle == "TL":
                anchor_item = br.bottomRight()
            elif handle == "TR":
                anchor_item = br.bottomLeft()
            elif handle == "BL":
                anchor_item = br.topRight()
            elif handle == "BR":
                anchor_item = br.topLeft()
            elif handle == "TC":
                anchor_item = QPointF(mid_x, br.bottom())
            elif handle == "BC":
                anchor_item = QPointF(mid_x, br.top())
            elif handle == "LC":
                anchor_item = QPointF(br.right(), mid_y)
            else: # "RC"
                anchor_item = QPointF(br.left(), mid_y)
                
            self._resize_anchor_item = anchor_item
            self._resize_anchor_scene = self.mapToScene(anchor_item)
            
            initial_vec = self._resize_start_pos - self._resize_anchor_scene
            self._resize_initial_dist = max(10.0, math.hypot(initial_vec.x(), initial_vec.y()))
            self._resize_initial_vec = initial_vec
            event.accept()
        else:
            self._is_resizing = False
            self._active_handle = None
            if event.button() == Qt.MouseButton.LeftButton:
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, "_is_resizing", False) and getattr(self, "_active_handle", None):
            anchor_scene = self._resize_anchor_scene
            cur_vec = event.scenePos() - anchor_scene
            cur_dist = math.hypot(cur_vec.x(), cur_vec.y())
            
            init_vec = self._resize_initial_vec
            dot = (cur_vec.x() * init_vec.x() + cur_vec.y() * init_vec.y())
            
            if dot <= 0:
                scale_factor = 0.05 / max(0.01, self._resize_start_scale)
            else:
                scale_factor = cur_dist / max(10.0, self._resize_initial_dist)
                
            new_scale = max(0.05, min(15.0, self._resize_start_scale * scale_factor))
            self.setScale(new_scale)
            
            new_anchor_scene = self.mapToScene(self._resize_anchor_item)
            shift = new_anchor_scene - anchor_scene
            self.setPos(self.pos() - shift)
            
            # Sync back to model so saving works
            if hasattr(self, 'model') and self.model:
                self.model.x = self.pos().x()
                self.model.y = self.pos().y()
                self.model.scale_w = new_scale
                self.model.scale_h = new_scale
                
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, "_is_resizing", False):
            self._is_resizing = False
            self._active_handle = None
            if self.scene() and hasattr(self.scene(), 'parent'):
                parent_ws = self.scene().parent()
                if hasattr(parent_ws, 'item_selected'):
                    parent_ws.item_selected.emit(self)
                if hasattr(parent_ws, 'items_changed'):
                    parent_ws.items_changed.emit(parent_ws.user_items)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
        if not getattr(self, "_hover_handle", None):
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseDoubleClickEvent(self, event):
        if self.canvas_workspace:
            self.hide()
            view = self.canvas_workspace.view
            scene_pos = self.scenePos()
            view_pos = view.mapFromScene(scene_pos)
            self.editor = TextEditorWidget(view_pos.x(), view_pos.y(), existing_model=self.model, parent=view, center_in_view=True)
            self.editor.editing_finished.connect(self._on_editing_finished)
            self.editor.show()
            self.editor.setFocus()
            
        super().mouseDoubleClickEvent(event)

    def _on_editing_finished(self, updated_model):
        if updated_model:
            self.model = updated_model
            self._load_image()
            self.show()
        else:
            if self.scene():
                self.scene().removeItem(self)
                if self.canvas_workspace and self in getattr(self.canvas_workspace, 'user_items', []):
                    self.canvas_workspace.user_items.remove(self)

    def update_text_properties(self):
        """Called by the properties panel to re-render the image with new font/size/color."""
        from components.write_to_image.image_renderer import render_text_to_image
        
        # Keep track of old scale to re-apply it properly
        old_scale = self.scale()
        
        image_path = render_text_to_image(
            text=self.model.text,
            font_family=self.model.font_family,
            font_size=self.model.font_size,
            color=self.model.color,
            id_str=self.model.id,
            is_bold=getattr(self.model, 'is_bold', False),
            is_italic=getattr(self.model, 'is_italic', False),
            is_underline=getattr(self.model, 'is_underline', False),
            text_effect=getattr(self.model, 'text_effect', 'none')
        )
        self.model.image_path = image_path
        self._load_image()
        
        if old_scale > 0 and old_scale != 1.0:
            self.setScale(old_scale)

    def to_dict(self):
        data = self.model.to_dict()
        data.update({
            "type": "WriteToImageGraphicsItem",
            "x": self.pos().x(),
            "y": self.pos().y(),
            "scale": self.scale(),
            "rotation": self.rotation(),
            "opacity": self.opacity(),
            "layer_name": self.layer_name,
            "anim_duration": self.anim_duration,
            "anim_delay": self.anim_delay
        })
        return data

    @classmethod
    def from_dict(cls, data):
        from components.write_to_image.models import WriteToImageModel
        model = WriteToImageModel(
            id=data.get("id", ""),
            name=data.get("name", "Text"),
            text=data.get("text", ""),
            font_family=data.get("font_family", "Arial"),
            font_size=data.get("font_size", 24),
            color=data.get("color", "#000000"),
            is_bold=data.get("is_bold", False),
            is_italic=data.get("is_italic", False),
            is_underline=data.get("is_underline", False),
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            image_path=data.get("image_path", ""),
            algorithm_style=data.get("algorithm_style", "linear"),
            text_effect=data.get("text_effect", "none")
        )
        model.sfx_name = data.get("sfx_name", "None")
        model.sfx_volume = data.get("sfx_volume", 100)
        
        item = cls(model=model, canvas_workspace=None)
        item.setPos(data.get("x", 0), data.get("y", 0))
        item.setScale(data.get("scale", 1.0))
        item.setRotation(data.get("rotation", 0))
        item.setOpacity(data.get("opacity", 1.0))
        item.layer_name = data.get("layer_name", "Text")
        item.anim_duration = data.get("anim_duration", 2.0)
        item.anim_delay = data.get("anim_delay", 0.0)
        return item

