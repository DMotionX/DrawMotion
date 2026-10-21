import math
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtCore import Qt, QRectF, QPointF, Property, Signal, QThread
from PySide6.QtGui import QPainter, QPen, QColor, QImage, QPixmap, QPainterPath
from PySide6.QtSvg import QSvgRenderer

# We reuse the stable Solid Reveal worker from the image engine to satisfy the 'Zero Risk' policy
from graphics.animated_image_item import PlannerWorker, _ACTIVE_WORKER_THREADS

class SVGCanvasItem(QGraphicsSvgItem):
    """
    Phase 2 & 3: SVG Animation via Solid Reveal Adapter.
    Provides infinite vector resolution when stationary, 
    and uses the stable Solid Reveal algorithm for timeline animation.
    """
    
    plan_started = Signal()
    plan_ready = Signal()

    def __init__(self, filepath: str):
        super().__init__()
        
        # Dynamically enforce thin shapes and remove fill
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                svg_data = f.read()
            import re
            # Enforce thin stroke
            if 'stroke-width' in svg_data:
                svg_data = re.sub(r'stroke-width="[^"]+"', 'stroke-width="2"', svg_data)
            else:
                # Add it to paths/rects if missing
                svg_data = svg_data.replace('<path ', '<path stroke-width="2" ')
                svg_data = svg_data.replace('<rect ', '<rect stroke-width="2" ')
                svg_data = svg_data.replace('<circle ', '<circle stroke-width="2" ')
                
            # Enforce no fill
            svg_data = re.sub(r'fill="[^"]+"', 'fill="none"', svg_data)
            
            # Keep original viewBox
            self._svg_renderer = QSvgRenderer(svg_data.encode('utf-8'))
            self.setSharedRenderer(self._svg_renderer)
        except Exception:
            # Fallback if any parsing fails
            super().__init__(filepath)
            
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setProperty("svg_filepath", filepath)
        
        # Timeline and Inspector required properties
        self._anim_duration = 3.0
        self._anim_delay = 0.0
        self._progress = 1.0
        self._total_calculated_time = 1.0
        self._layer_name = "SVG Shape"
        self.drawing_style = "Solid Reveal"
        self.anim_type = "Draw"
        
        self._qimage = None
        self._scribble_buffer = None
        self._composite_buffer = None
        self._timed_segments = []
        self._cached_scale_ratio = 1.0
        
        self._last_drawn_progress = -1.0
        self._plan_loaded = False
        self._is_loading_plan = False
        
        # Resizing state
        self._resize_dir = None
        self._is_resizing = False
        self._resize_start_pos = QPointF()
        self._resize_start_scale = 1.0
        
        self._worker = None
        self._thread = None

    def type(self):
        return QGraphicsItem.UserType + 100
        
    # --- Animator Engine Compat ---
    @property
    def anim_duration(self):
        return self._anim_duration

    @anim_duration.setter
    def anim_duration(self, val):
        self.set_anim_duration(val)
        
    @property
    def anim_delay(self):
        return self._anim_delay

    @anim_delay.setter
    def anim_delay(self, val):
        self._anim_delay = val
        
    def get_progress(self):
        return self._progress
        
    def set_progress(self, p):
        is_exporting = getattr(self, '_is_exporting', False)
        threshold = 1e-7 if is_exporting else 0.0001
        if abs(p - self._progress) > threshold or (p >= 1.0 and self._progress < 1.0):
            self._progress = p
            if p <= 0.0001:
                self._last_drawn_progress = -1.0
                self._active_paint_idx = 0
                if self._scribble_buffer:
                    self._scribble_buffer.fill(Qt.GlobalColor.transparent)
            self.update()
        
    progress = Property(float, get_progress, set_progress)
    
    def _get_effective_progress(self):
        return self._progress

    def _get_exact_target(self):
        if not self._timed_segments or self._progress <= 0:
            return self.boundingRect().center()
        
        p = self._get_effective_progress()
        if p >= 1.0:
            if self._timed_segments:
                return self._timed_segments[-1]["points"][-1]
            return self.boundingRect().center()

        ct = p * self._total_calculated_time
        for seg in self._timed_segments:
            if seg["start_time"] <= ct <= seg["end_time"]:
                pts = seg["points"]
                if not pts:
                    continue
                if len(pts) == 1:
                    return pts[0]
                active_dur = seg.get("active_duration", max(0.001, seg["duration"]))
                local_time = min(active_dur, ct - seg["start_time"])
                frac = max(0.0, min(1.0, local_time / active_dur if active_dur > 0 else 1.0))
                
                # Continuous sub-pixel linear interpolation
                if len(pts) == 2:
                    p0, p1 = pts[0], pts[1]
                    return QPointF(p0.x() + (p1.x() - p0.x()) * frac,
                                   p0.y() + (p1.y() - p0.y()) * frac)
                
                float_idx = frac * (len(pts) - 1)
                base_idx = int(float_idx)
                if base_idx >= len(pts) - 1:
                    return pts[-1]
                sub_frac = float_idx - base_idx
                p0, p1 = pts[base_idx], pts[base_idx + 1]
                return QPointF(p0.x() + (p1.x() - p0.x()) * sub_frac,
                               p0.y() + (p1.y() - p0.y()) * sub_frac)
            elif seg["start_time"] > ct:
                break

        if self._timed_segments:
            return self._timed_segments[-1]["points"][-1]
        return self.boundingRect().center()

    def get_tip_position(self):
        target = self._get_exact_target()
        return target

    def set_anim_duration(self, duration: float):
        if self._anim_duration != duration:
            self._anim_duration = duration
            self._plan_loaded = False
            self._active_paint_idx = 0
            self._last_drawn_progress = -1.0
            self.build_plan_async()

    def set_drawing_style(self, style: str):
        if self.drawing_style != style:
            self.drawing_style = style
            self._plan_loaded = False
            self.build_plan_async()

    # --- Phase 2 & 3: Animation Building ---
    def build_plan_async(self):
        if self._is_loading_plan:
            return

        self._is_loading_plan = True
        self.plan_started.emit()
        
        if self._thread is not None:
            try:
                self._worker.finished.disconnect(self._on_plan_ready)
            except Exception:
                pass
            old_thread = self._thread
            self._thread = None
            self._worker = None
            old_thread.quit()
            old_thread.wait(500)

        self._last_drawn_progress = -1.0
        
        # Render the SVG to a high-res QImage for perfect pixel extraction
        ANALYSIS_SIZE = 1200
        br = self.boundingRect()
        
        if br.width() <= 0 or br.height() <= 0:
            self._is_loading_plan = False
            return
            
        scale_ratio = min(ANALYSIS_SIZE / br.width(), ANALYSIS_SIZE / br.height())
        new_w = int(br.width() * scale_ratio)
        new_h = int(br.height() * scale_ratio)
        
        # Render pure SVG to QImage
        self._qimage = QImage(new_w, new_h, QImage.Format.Format_ARGB32_Premultiplied)
        self._qimage.fill(Qt.GlobalColor.transparent)
        painter = QPainter(self._qimage)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # We use the item's internal renderer to render at the specific high-res size
        renderer = self.renderer()
        if renderer and renderer.isValid():
            renderer.render(painter, QRectF(0, 0, new_w, new_h))
        painter.end()
        
        self._cached_scale_ratio = scale_ratio
        
        self._scribble_buffer = QImage(new_w, new_h, QImage.Format.Format_ARGB32_Premultiplied)
        self._scribble_buffer.fill(Qt.GlobalColor.transparent)
        self._composite_buffer = QImage(new_w, new_h, QImage.Format.Format_ARGB32_Premultiplied)
        self._composite_buffer.fill(Qt.GlobalColor.transparent)
        
        inv_scale = 1.0 / self._cached_scale_ratio

        old_t = getattr(self, '_thread', None)
        if old_t is not None:
            try:
                import shiboken6
                if shiboken6.isValid(old_t) and old_t.isRunning():
                    return
            except Exception:
                pass

        # FIX: We ALWAYS force SVGs to use "Solid Reveal" (Clean Outline).
        # Other algorithms (like Line Art or Professional) use Canny & Thinning, 
        # which causes massive lag on vectors. "Solid Reveal" is instantaneous and perfect!
        self._worker = PlannerWorker(self._qimage, self._anim_duration, "Solid Reveal", inv_scale)
        self._thread = QThread()
        self._thread.setObjectName(f"SVGCanvasPlanner_{id(self)}")
        _ACTIVE_WORKER_THREADS.append(self._thread)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_plan_ready)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._on_worker_thread_finished)
        self._thread.start()

    def _on_worker_thread_finished(self):
        thread = self.sender()
        if thread:
            try:
                thread.wait(500)
            except Exception:
                pass
            if thread in _ACTIVE_WORKER_THREADS:
                try:
                    _ACTIVE_WORKER_THREADS.remove(thread)
                except ValueError:
                    pass
        if getattr(self, '_thread', None) is thread:
            self._thread = None
            self._worker = None

    def cleanup(self):
        """Safely stops any active background planning thread before item is removed."""
        t = getattr(self, '_thread', None)
        if t is not None:
            try:
                if t.isRunning():
                    t.quit()
                    t.wait(500)
            except Exception:
                pass
            if t in _ACTIVE_WORKER_THREADS:
                try:
                    _ACTIVE_WORKER_THREADS.remove(t)
                except ValueError:
                    pass
            self._thread = None
            self._worker = None

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass


    def _on_plan_ready(self, segments):
        self._timed_segments = segments
        self._total_calculated_time = max(0.01, segments[-1]["end_time"] if segments else 1.0)
        self._plan_loaded = True
        self._is_loading_plan = False
        self._last_drawn_progress = -1.0
        self._active_paint_idx = 0
        self.update()
        self.plan_ready.emit()

    # --- Rendering ---
    def paint(self, painter: QPainter, option, widget=None):
        painter.save()
        
        p = self._progress
        
        if p >= 1.0 or not self._plan_loaded:
            # PERFECT VECTOR RENDERING when finished or idle!
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            super().paint(painter, option, widget)
        elif p <= 0.0:
            pass # Hidden
        else:
            # ANIMATED RASTER MASKING during timeline playback
            self._paint_animated(painter, p)

        painter.restore()
        
        if self.isSelected():
            self._paint_selection(painter)

    def _paint_animated(self, painter: QPainter, p: float):
        current_time = p * self._total_calculated_time
        last_time = max(0.0, self._last_drawn_progress * self._total_calculated_time)

        start_idx = getattr(self, '_active_paint_idx', 0)
        if self._last_drawn_progress < 0 or p < self._last_drawn_progress - 0.001 or start_idx >= len(self._timed_segments):
            self._scribble_buffer.fill(Qt.GlobalColor.transparent)
            last_time = 0.0
            start_idx = 0
            self._active_paint_idx = 0

        buf_painter = QPainter(self._scribble_buffer)
        buf_painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Scale the painter so it matches the high-res buffer but draws in local coordinates
        scale_ratio = self._cached_scale_ratio
        buf_painter.scale(scale_ratio, scale_ratio)

        for i in range(start_idx, len(self._timed_segments)):
            segment = self._timed_segments[i]
            if segment["end_time"] <= last_time:
                self._active_paint_idx = i
                continue
            if segment["start_time"] > current_time:
                break

            pts = segment["points"]
            if len(pts) < 2:
                continue

            color = QColor(Qt.GlobalColor.black)
            color.setAlphaF(segment.get("opacity", 1.0))
            pen = QPen(color, segment.get("width", 15.0))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            buf_painter.setPen(pen)

            seg_dur = max(0.001, segment["duration"])
            if last_time >= segment["end_time"]:
                continue
                
            if current_time >= segment["end_time"] and last_time <= segment["start_time"]:
                buf_painter.drawPolyline(pts)
            elif current_time >= segment["end_time"]:
                active_dur = segment.get("active_duration", seg_dur)
                seg_start  = max(0.0, last_time - segment["start_time"])
                p_start = seg_start / active_dur if active_dur > 0 else 1.0
                idx_start = int(p_start * (len(pts) - 1))
                buf_painter.drawPolyline(pts[idx_start:])
            else:
                active_dur = segment.get("active_duration", seg_dur)
                local_end  = min(active_dur, current_time - segment["start_time"])
                seg_start  = max(0.0, last_time - segment["start_time"])
                p_end = local_end / active_dur if active_dur > 0 else 1.0
                p_start = seg_start / active_dur if active_dur > 0 else 1.0
                idx_start = int(p_start * (len(pts) - 1))
                
                if len(pts) == 2:
                    p0, p1 = pts[0], pts[1]
                    cur_tip = QPointF(p0.x() + (p1.x() - p0.x()) * p_end,
                                      p0.y() + (p1.y() - p0.y()) * p_end)
                    buf_painter.drawLine(p0, cur_tip)
                else:
                    float_idx = p_end * (len(pts) - 1)
                    idx_end = int(float_idx)
                    sub_frac = float_idx - idx_end
                    
                    if idx_end > idx_start:
                        buf_painter.drawPolyline(pts[idx_start:idx_end + 1])
                    
                    if idx_end < len(pts) - 1 and sub_frac > 0.001:
                        p_a = pts[idx_end]
                        p_b = pts[idx_end + 1]
                        cur_tip = QPointF(p_a.x() + (p_b.x() - p_a.x()) * sub_frac,
                                          p_a.y() + (p_b.y() - p_a.y()) * sub_frac)
                        buf_painter.drawLine(p_a, cur_tip)

        buf_painter.end()
        self._last_drawn_progress = p

        # Composite the scribble mask with the high-res QImage
        self._composite_buffer.fill(Qt.GlobalColor.transparent)
        comp_painter = QPainter(self._composite_buffer)
        comp_painter.drawImage(0, 0, self._scribble_buffer)
        comp_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        comp_painter.drawImage(0, 0, self._qimage)
        comp_painter.end()

        # Draw the composite buffer downscaled to the item's original bounding rect
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        br = self.boundingRect()
        painter.drawImage(br, self._composite_buffer, QRectF(0, 0, self._composite_buffer.width(), self._composite_buffer.height()))

    def _paint_selection(self, painter: QPainter):
        painter.save()
        
        pen = QPen(QColor(33, 150, 243)) # #2196F3
        pen.setStyle(Qt.PenStyle.SolidLine)
        pen.setWidth(2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        br = self.boundingRect()
        painter.drawRect(br)

        painter.setBrush(QColor("#FFFFFF"))
        h_pen = QPen(QColor("#2196F3"))
        h_pen.setWidth(1)
        h_pen.setCosmetic(True)
        painter.setPen(h_pen)
        
        hs = 8 / self.scale() if self.scale() != 0 else 8
        for cx, cy in [
            (br.left(), br.top()), 
            (br.right(), br.top()),
            (br.left(), br.bottom()), 
            (br.right(), br.bottom())
        ]:
            painter.drawRect(QRectF(cx - hs/2, cy - hs/2, hs, hs))
            
        painter.restore()

    def _get_exact_target(self):
        if not self._timed_segments or self._progress <= 0:
            return self.boundingRect().center()
        
        p = self._progress
        if p >= 1.0:
            if self._timed_segments:
                return self._timed_segments[-1]["points"][-1]
            return self.boundingRect().center()
            
        ct = p * self._total_calculated_time
        start_idx = getattr(self, '_active_target_idx', 0)
        if p < getattr(self, '_last_target_p', 0.0) - 0.001 or start_idx >= len(self._timed_segments):
            start_idx = 0
            self._active_target_idx = 0
            
        self._last_target_p = p
        
        for i in range(start_idx, len(self._timed_segments)):
            seg = self._timed_segments[i]
            if seg["start_time"] <= ct <= seg["end_time"]:
                self._active_target_idx = i
                pts = seg["points"]
                active_dur = seg.get("active_duration", max(0.001, seg["duration"]))
                local_time = min(active_dur, ct - seg["start_time"])
                frac = local_time / active_dur if active_dur > 0 else 1.0
                idx = int(frac * (len(pts) - 1))
                return pts[min(idx, len(pts)-1)]
            elif seg["start_time"] > ct:
                break
                
        if self._timed_segments:
            return self._timed_segments[-1]["points"][-1]
        return self.boundingRect().center()

    def get_tip_position(self):
        return self._get_exact_target()

    # ── Interactive Resizing ──────────────────────────────────────────────────

    def shape(self):
        path = QPainterPath()
        s = self.scale() if self.scale() > 0 else 1.0
        pad = 20.0 / s
        path.addRect(self.boundingRect().adjusted(-pad, -pad, pad, pad))
        return path

    def hoverMoveEvent(self, event):
        pos = event.pos()
        br = self.boundingRect()
        s = self.scale() if self.scale() > 0 else 1.0
        hs = 20.0 / s
        
        tl = QRectF(br.left() - hs, br.top() - hs, hs * 2, hs * 2)
        tr = QRectF(br.right() - hs, br.top() - hs, hs * 2, hs * 2)
        bl = QRectF(br.left() - hs, br.bottom() - hs, hs * 2, hs * 2)
        br_rect = QRectF(br.right() - hs, br.bottom() - hs, hs * 2, hs * 2)

        if tl.contains(pos):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            self._hover_handle = "TL"
        elif br_rect.contains(pos):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            self._hover_handle = "BR"
        elif tr.contains(pos):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            self._hover_handle = "TR"
        elif bl.contains(pos):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            self._hover_handle = "BL"
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._hover_handle = None
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        handle = getattr(self, "_hover_handle", None)
        if handle and event.button() == Qt.MouseButton.LeftButton:
            self._is_resizing = True
            self._active_handle = handle
            self._resize_start_pos = event.scenePos()
            self._resize_start_scale = self.scale()
            
            br = self.boundingRect()
            if handle == "TL":
                anchor_item = br.bottomRight()
            elif handle == "TR":
                anchor_item = br.bottomLeft()
            elif handle == "BL":
                anchor_item = br.topRight()
            else: # "BR"
                anchor_item = br.topLeft()
                
            self._resize_anchor_item = anchor_item
            self._resize_anchor_scene = self.mapToScene(anchor_item)
            
            initial_vec = self._resize_start_pos - self._resize_anchor_scene
            self._resize_initial_dist = max(10.0, math.hypot(initial_vec.x(), initial_vec.y()))
            self._resize_initial_vec = initial_vec
            event.accept()
        else:
            self._is_resizing = False
            self._active_handle = None
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

    def to_dict(self):
        return {
            "type": "SVGCanvasItem",
            "x": self.pos().x(),
            "y": self.pos().y(),
            "scale": self.scale(),
            "rotation": self.rotation(),
            "opacity": self.opacity(),
            "anim_duration": self._anim_duration,
            "anim_delay": self._anim_delay,
            "layer_name": self._layer_name,
            "drawing_style": self.drawing_style,
            "anim_type": self.anim_type,
            "sfx_name": getattr(self, "sfx_name", "None"),
            "sfx_volume": getattr(self, "sfx_volume", 100),
            "svg_filepath": self.property("svg_filepath")
        }

    @classmethod
    def from_dict(cls, data):
        svg_filepath = data.get("svg_filepath", "")
        item = cls(svg_filepath)
        
        item.setPos(data.get("x", 0), data.get("y", 0))
        item.setScale(data.get("scale", 1.0))
        item.setRotation(data.get("rotation", 0))
        item.setOpacity(data.get("opacity", 1.0))
        item._anim_duration = data.get("anim_duration", 3.0)
        item._anim_delay = data.get("anim_delay", 0.0)
        item._layer_name = data.get("layer_name", "SVG Shape")
        item.drawing_style = data.get("drawing_style", "Solid Reveal")
        item.anim_type = data.get("anim_type", "Draw")
        item.sfx_name = data.get("sfx_name", "None")
        item.sfx_volume = data.get("sfx_volume", 100)
        
        return item

    def cleanup(self):
        """Safely stops and waits for any background planner threads before object destruction."""
        try:
            t = getattr(self, '_thread', None)
            if t is not None:
                try:
                    import shiboken6
                    if shiboken6.isValid(t) and t.isRunning():
                        t.quit()
                        t.wait(500)
                except Exception:
                    pass
                self._thread = None
                self._worker = None
        except Exception:
            pass

    def __del__(self):
        self.cleanup()

