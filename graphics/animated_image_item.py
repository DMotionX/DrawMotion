from PySide6.QtWidgets import QGraphicsObject
from PySide6.QtCore import Qt, QRectF, Property, QPointF, QSize, QThread, Signal, QObject
from PySide6.QtGui import QPainter, QPixmap, QImage, QPen, QColor, QPainterPath, QBrush
import math

def ease_in_out_cubic(t):
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return 4 * t * t * t
    return 1 - math.pow(-2 * t + 2, 3) / 2

_ACTIVE_WORKER_THREADS = []

class PlannerWorker(QObject):
    finished = Signal(list)

    def __init__(self, qimage, duration, style_name, inv_scale=1.0, rtl=False, is_text=False):
        super().__init__()
        self.qimage     = qimage
        self.duration   = duration
        self.style_name = style_name
        self.inv_scale  = inv_scale
        self.rtl        = rtl
        self.is_text    = is_text

    def run(self):
        try:
            from core.drawing_engine.algorithms.factory import AlgorithmFactory
            algorithm = AlgorithmFactory.get_algorithm(self.style_name)
            
            # Pass effective RTL direction to algorithm
            timed_segments = algorithm.generate_plan(self.qimage, self.duration, rtl=self.rtl)

            import math

            refined_segments = []
            
            for segment in timed_segments:
                pts = segment["points"]
                if not pts: 
                    continue
                    
                scaled_pts = [QPointF(p.x() * self.inv_scale, p.y() * self.inv_scale) for p in pts]
                base_width = segment.get("width", 15.0) * self.inv_scale
                
                # Modern vector algorithms (Professional, Sketch, Educational, etc.) already manage intentional strokes
                # and explicit in-air travel flights. Preserving them eliminates white gaps and chopped lines.
                if segment.get("type") in ["stroke", "travel"] or self.style_name in [
                    "Professional", "Sketch", "Educational", "Organic Sketch", "Hatch Shading", "Clean Outline", "Line Art (Skeleton)"
                ]:
                    new_seg = dict(segment)
                    new_seg["points"] = scaled_pts
                    new_seg["width"] = base_width
                    new_seg.setdefault("start_time", 0.0)
                    new_seg.setdefault("duration", self.duration)
                    new_seg.setdefault("end_time", new_seg["start_time"] + new_seg["duration"])
                    refined_segments.append(new_seg)
                    continue

                # Fallback jump slicer for legacy raster algorithms
                threshold = max(20.0, base_width) * 1.15 
                
                sub_segments = []
                current_sub = [scaled_pts[0]]
                
                for i in range(1, len(scaled_pts)):
                    dist = math.hypot(scaled_pts[i].x() - scaled_pts[i-1].x(), scaled_pts[i].y() - scaled_pts[i-1].y())
                    if dist > threshold:
                        # Close current drawing segment
                        if len(current_sub) == 1:
                            current_sub.append(QPointF(current_sub[0].x() + 1, current_sub[0].y()))
                        sub_segments.append({"points": current_sub, "is_jump": False})
                        
                        # Add the jump as an invisible segment
                        sub_segments.append({"points": [scaled_pts[i-1], scaled_pts[i]], "is_jump": True})
                        
                        current_sub = [scaled_pts[i]]
                    else:
                        current_sub.append(scaled_pts[i])
                        
                if len(current_sub) > 0:
                    if len(current_sub) == 1:
                        current_sub.append(QPointF(current_sub[0].x() + 1, current_sub[0].y()))
                    sub_segments.append({"points": current_sub, "is_jump": False})
                
                # Distribute the original segment's time among the sub_segments based on physical length
                orig_start = segment["start_time"]
                orig_dur = segment["duration"]
                
                total_len = 0.0
                for sub in sub_segments:
                    # Calculate physical length of this sub segment
                    s_pts = sub["points"]
                    length = sum(math.hypot(s_pts[j].x() - s_pts[j-1].x(), s_pts[j].y() - s_pts[j-1].y()) for j in range(1, len(s_pts)))
                    sub["length"] = max(0.01, length) # Prevent divide by zero
                    total_len += sub["length"]
                    
                curr_time = orig_start
                for sub in sub_segments:
                    ratio = sub["length"] / total_len if total_len > 0 else 0
                    dur = orig_dur * ratio
                    
                    # Create a completely new segment dictionary to inherit styling (like type, original opacity)
                    new_seg = dict(segment)
                    new_seg["points"] = sub["points"]
                    new_seg["length"] = sub["length"]
                    new_seg["duration"] = dur
                    new_seg["active_duration"] = dur
                    new_seg["start_time"] = curr_time
                    new_seg["end_time"] = curr_time + dur
                    new_seg["width"] = base_width
                    
                    # If this is a jump, make it completely transparent so it doesn't bleed
                    if sub["is_jump"]:
                        new_seg["opacity"] = 0.0
                        
                    refined_segments.append(new_seg)
                    curr_time += dur

            self.finished.emit(refined_segments)
        except Exception as e:
            import traceback
            print(f"Error in PlannerWorker: {e}")
            traceback.print_exc()
            self.finished.emit([])


class AnimatedImageItem(QGraphicsObject):
    plan_started = Signal()
    plan_ready = Signal()

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._pixmap         = pixmap
        self._progress       = 1.0   # show full image by default
        self._anim_duration  = 2.0
        self._anim_delay     = 0.0
        self._layer_name     = "Image"
        self.drawing_style   = "Solid Reveal"
        self.drawing_direction = "auto"
        self.anim_type       = "Draw"
        self.anim_dir        = "From Left"
        self.anim_easing     = "Linear"
        self.sfx_name        = "None"
        self.sfx_volume      = 100

        # High-quality downsampling for huge images to avoid aliasing pixelation
        # Limit to 1080 internally to prevent heavy QPixmap composition lag at 60 FPS
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

        # Visually fit large images in the canvas without destroying pixel data
        max_size = 400.0
        if w > max_size or h > max_size:
            self.setScale(min(max_size / w, max_size / h))

        self.setFlags(
            QGraphicsObject.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsObject.GraphicsItemFlag.ItemIsMovable |
            QGraphicsObject.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

        self._timed_segments          = []
        self._total_calculated_time   = 1.0
        
        # FIX: Use QImage with Premultiplied Alpha to prevent edge pixelation on transparent PNGs!
        self._qimage = self._pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        self._scribble_buffer = QImage(self._pixmap.size(), QImage.Format.Format_ARGB32_Premultiplied)
        self._scribble_buffer.fill(Qt.GlobalColor.transparent)
        self._composite_buffer = QImage(self._pixmap.size(), QImage.Format.Format_ARGB32_Premultiplied)
        self._composite_buffer.fill(Qt.GlobalColor.transparent)
        
        self._last_drawn_progress     = -1.0
        self._plan_loaded             = False
        
        from PySide6.QtCore import QTimer
        self._is_loading_plan = False
        self._loading_angle = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._update_loading_angle)

        self._thread = None
        self._worker = None
        
    def _update_loading_angle(self):
        self._loading_angle = (self._loading_angle + 20) % 360
        self.update()

    # ── Public API ────────────────────────────────────────────────────────────

    def replace_image(self, new_pixmap: QPixmap):
        self._pixmap = new_pixmap
        
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
            
        self._qimage = self._pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
        self._scribble_buffer = QImage(self._pixmap.size(), QImage.Format.Format_ARGB32_Premultiplied)
        self._scribble_buffer.fill(Qt.GlobalColor.transparent)
        self._composite_buffer = QImage(self._pixmap.size(), QImage.Format.Format_ARGB32_Premultiplied)
        self._composite_buffer.fill(Qt.GlobalColor.transparent)
        
        self.prepareGeometryChange()
        self._last_drawn_progress = -1.0
        self._plan_loaded = False
        self.build_plan_async()
        self.update()

    def set_anim_duration(self, duration: float):
        if self._anim_duration != duration:
            self._anim_duration = duration
            self._plan_loaded = False
            self._active_paint_idx = 0
            self._active_target_idx = 0
            self._last_drawn_progress = -1.0
            self.build_plan_async()

    def set_drawing_style(self, style_name: str):
        if self.drawing_style != style_name:
            self.drawing_style = style_name
            self._plan_loaded  = False
            self._timed_segments = []
            self.build_plan_async()

    def set_drawing_direction(self, direction: str):
        if getattr(self, 'drawing_direction', 'auto') != direction:
            self.drawing_direction = direction
            self._plan_loaded  = False
            self._timed_segments = []
            self.build_plan_async()

    def build_plan_async(self):
        """Start background plan building. Call this before Play."""
        if self._is_loading_plan:
            self._needs_rebuild = True
            return

        self._needs_rebuild = False

        self._is_loading_plan = True
        self._loading_timer.start(30) # Smooth 30ms animation
        self.plan_started.emit()
        
        old_thread = getattr(self, '_thread', None)
        if old_thread is not None:
            try:
                import shiboken6
                if shiboken6.isValid(old_thread) and old_thread.isRunning():
                    try:
                        if getattr(self, '_worker', None) is not None:
                            self._worker.finished.disconnect()
                    except Exception:
                        pass
                    old_thread.quit()
                    old_thread.wait(500)
            except Exception:
                pass
            finally:
                self._thread = None
                self._worker = None

        self._scribble_buffer.fill(Qt.GlobalColor.transparent)
        self._last_drawn_progress = -1.0

        # KEY FIX: Downscale and convert to QImage on MAIN thread.
        # We use a large enough size (1200) to preserve small text and thin lines, 
        # but small enough to prevent toImage() from freezing the UI on 4K images.
        ANALYSIS_SIZE = 1200
        w, h = self._pixmap.width(), self._pixmap.height()
        scale_ratio = 1.0
        
        if not hasattr(self, '_analysis_image') or getattr(self, '_cached_pixmap_id', None) != id(self._pixmap):
            if w > ANALYSIS_SIZE or h > ANALYSIS_SIZE:
                scale_ratio = min(ANALYSIS_SIZE / w, ANALYSIS_SIZE / h)
                new_w = int(w * scale_ratio)
                new_h = int(h * scale_ratio)
                analysis_pixmap = self._pixmap.scaled(
                    new_w, new_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                analysis_pixmap = self._pixmap
                
            self._analysis_image = analysis_pixmap.toImage()
            self._cached_pixmap_id = id(self._pixmap)
            self._cached_scale_ratio = scale_ratio
        
        qimage = self._analysis_image
        inv_scale = 1.0 / self._cached_scale_ratio

        # Determine effective RTL direction (Auto / Manual RTL / Manual LTR)
        direction = getattr(self, 'drawing_direction', 'auto')
        if direction == "rtl":
            effective_rtl = True
        elif direction == "ltr":
            effective_rtl = False
        else:
            try:
                from core.drawing_engine.script_detector import detect_script_direction
                source_txt = getattr(self, 'source_text', None)
                effective_rtl = (detect_script_direction(qimage, source_txt) == "rtl")
            except Exception:
                effective_rtl = False

        old_t = getattr(self, '_thread', None)
        if old_t is not None:
            try:
                import shiboken6
                if shiboken6.isValid(old_t) and old_t.isRunning():
                    self._needs_rebuild = True
                    return
            except Exception:
                self._thread = None
                self._worker = None

        self._worker = PlannerWorker(qimage, self._anim_duration, self.drawing_style, inv_scale, rtl=effective_rtl)
        self._thread = QThread()
        self._thread.setObjectName(f"AnimatedImagePlanner_{id(self)}")
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
        self._timed_segments        = segments
        last_end = segments[-1].get("end_time", self._anim_duration) if segments else 1.0
        self._total_calculated_time = max(0.01, float(last_end))
        self._plan_loaded           = True
        self._last_drawn_progress   = -1.0
        self._active_paint_idx      = 0
        self._active_target_idx     = 0
        
        self._is_loading_plan       = False
        self._loading_timer.stop()
        
        if getattr(self, '_needs_rebuild', False):
            self._needs_rebuild = False
            self._plan_loaded = False
            self.build_plan_async()
            return
            
        # Resume drawing from the EXACT progress the timeline expects,
        # instead of forcing 1.0 which causes a visual flash and rewind bug!
        self.set_progress(self._progress)
        self.update()
        self.plan_ready.emit()

    # ── Properties for Animator Engine ───────────────────────────────────────

    @property
    def anim_duration(self):
        return self._anim_duration

    @anim_duration.setter
    def anim_duration(self, v):
        self.set_anim_duration(v)

    @property
    def anim_delay(self):
        return self._anim_delay

    @anim_delay.setter
    def anim_delay(self, v):
        self._anim_delay = v

    @property
    def layer_name(self):
        return self._layer_name

    @layer_name.setter
    def layer_name(self, v):
        self._layer_name = v

    def get_progress(self):
        return self._progress

    def set_progress(self, v):
        is_exporting = getattr(self, '_is_exporting', False)
        threshold = 1e-7 if is_exporting else 0.0001
        if abs(v - self._progress) > threshold or (v >= 1.0 and self._progress < 1.0):
            self._progress = v
            if v <= 0.0001:
                self._last_drawn_progress = -1.0
                self._active_paint_idx = 0
                self._active_target_idx = 0
                self._scribble_buffer.fill(Qt.GlobalColor.transparent)
            self.update()

    progress = Property(float, get_progress, set_progress)

    # ── Bounding rect ─────────────────────────────────────────────────────────

    def boundingRect(self):
        return QRectF(0, 0, self._pixmap.width(), self._pixmap.height())

    def _get_effective_progress(self):
        if not self._timed_segments:
            return self._progress
            
        if not hasattr(self, '_total_length'):
            self._total_length = 0.0
            import math
            for seg in self._timed_segments:
                pts = seg["points"]
                for i in range(1, len(pts)):
                    dx = pts[i].x() - pts[i-1].x()
                    dy = pts[i].y() - pts[i-1].y()
                    self._total_length += math.hypot(dx, dy)
                    
        # The progress must exactly match the timeline (and thus the hand's tip_position)
        # to ensure perfect synchronization. Do not override the user's duration.
        return self._progress

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        p = self._get_effective_progress()

        if not self._plan_loaded:
            painter.drawPixmap(0, 0, self._pixmap)
            
            if self._is_loading_plan:
                painter.fillRect(self.boundingRect(), QColor(0, 0, 0, 150))
                pen = QPen(QColor(255, 255, 255))
                inv_scale = 1.0 / self.scale() if self.scale() > 0 else 1.0
                pen.setWidth(int(4 * inv_scale))
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                cx = self.boundingRect().center().x()
                cy = self.boundingRect().center().y()
                r = 30 * inv_scale
                painter.drawArc(int(cx - r), int(cy - r), int(r * 2), int(r * 2), self._loading_angle * 16, 270 * 16)
                
        elif p <= 0.0:
            pass  # hidden
        elif p >= 1.0:
            # High-performance fast-path: image is 100% complete!
            # Render pixmap directly with zero compositing overhead
            painter.drawPixmap(0, 0, self._pixmap)
        else:
            self._paint_animated(painter, p)

        if self.isSelected():
            self._paint_selection(painter)

        painter.restore()

    def _paint_animated(self, painter, p):
        current_time = p * self._total_calculated_time
        last_time    = max(0.0, self._last_drawn_progress * self._total_calculated_time)

        start_idx = getattr(self, '_active_paint_idx', 0)
        if self._last_drawn_progress < 0 or p < self._last_drawn_progress - 0.001 or start_idx >= len(self._timed_segments):
            # Rewound or new plan — clear buffer and reset start index
            self._scribble_buffer.fill(Qt.GlobalColor.transparent)
            last_time = 0.0
            start_idx = 0
            self._active_paint_idx = 0

        buf_painter = QPainter(self._scribble_buffer)
        buf_painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for i in range(start_idx, len(self._timed_segments)):
            segment = self._timed_segments[i]
            if segment["end_time"] <= last_time:
                self._active_paint_idx = i
                continue
            if segment["start_time"] > current_time:
                break

            if segment.get("type") == "travel" or segment.get("opacity", 1.0) <= 0.0:
                continue

            pts = segment["points"]
            if len(pts) < 2:
                continue

            color = QColor(Qt.GlobalColor.black)
            color.setAlphaF(segment.get("opacity", 1.0))
            
            # For stylistic modes, the width is calculated by the algorithm and scaled by inv_scale.
            base_width = segment.get("width", 15.0)
            
            # Since all modes are now shape-fillers, we use the base_width directly
            final_width = base_width
                
            pen = QPen(color, final_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            buf_painter.setPen(pen)

            seg_dur    = max(0.001, segment["duration"])
            
            # If the segment was completely skipped over in a single frame jump,
            # we must ensure it gets drawn entirely instead of being discarded.
            if last_time >= segment["end_time"]:
                # This segment is completely in the past, it was drawn in a previous frame
                continue
                
            if current_time >= segment["end_time"] and last_time <= segment["start_time"]:
                # The frame jumped COMPLETELY over this segment: draw all of it
                buf_painter.drawPolyline(pts)
            elif current_time >= segment["end_time"]:
                # Segment was partially drawn in previous frame and finishes now
                active_dur = segment.get("active_duration", seg_dur)
                seg_start  = max(0.0, last_time - segment["start_time"])
                p_start = seg_start / active_dur if active_dur > 0 else 1.0
                idx_start = int(p_start * (len(pts) - 1))
                buf_painter.drawPolyline(pts[idx_start:])
            else:
                # Active segment currently being drawn: continuous fluid ink flow
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
                    
                    if idx_end < len(pts) - 1 and sub_frac > 1e-5:
                        p_a = pts[idx_end]
                        p_b = pts[idx_end + 1]
                        cur_tip = QPointF(p_a.x() + (p_b.x() - p_a.x()) * sub_frac,
                                          p_a.y() + (p_b.y() - p_a.y()) * sub_frac)
                        buf_painter.drawLine(p_a, cur_tip)

        buf_painter.end()
        self._last_drawn_progress = p

        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # All styles use the Solid Reveal approach (masking):
        # We scribble thick black patterns into _scribble_buffer, and use it as an alpha mask 
        # to reveal the clean, perfect original high-res image.
        self._composite_buffer.fill(Qt.GlobalColor.transparent)
        comp_painter = QPainter(self._composite_buffer)
        comp_painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        comp_painter.drawImage(0, 0, self._scribble_buffer)
        comp_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        comp_painter.drawImage(0, 0, self._qimage)
        comp_painter.end()
        painter.drawImage(0, 0, self._composite_buffer)
        
        # Color Pop / Fade-In effect smoothed across absolute end to ensure clean final render
        fade_start = 0.995
        if p > fade_start:
            fade_opacity = (p - fade_start) / (1.0 - fade_start)
            # Ensure it doesn't exceed 1.0 due to float precision
            fade_opacity = min(1.0, max(0.0, fade_opacity))
            painter.setOpacity(fade_opacity)
            painter.drawImage(0, 0, self._qimage)
            painter.setOpacity(1.0)

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
        for cx, cy in [(br.left(), br.top()), (br.right(), br.top()),
                       (br.left(), br.bottom()), (br.right(), br.bottom())]:
            painter.drawRect(QRectF(cx - hs/2, cy - hs/2, hs, hs))
            
        # Draw the order badge
        if hasattr(self, 'draw_order') and self.draw_order is not None:
            parent = self.parentItem()
            if parent:
                siblings = [item for item in parent.childItems() if item.__class__.__name__ == 'AnimatedImageItem']
                if len(siblings) <= 1:
                    return # Do not draw badge if there's only one image
                    
            # We want the badge to be readable regardless of scale
            inv_scale = 1.0 / self.scale() if self.scale() > 0 else 1.0
            badge_radius = 12 * inv_scale
            font_size = 12 * inv_scale
            
            painter.setBrush(QColor("#F44336")) # Red badge
            painter.setPen(Qt.PenStyle.NoPen)
            # Draw INSIDE the bounding rect so Qt clears it properly when moving
            center = QPointF(br.left() + badge_radius + (4 * inv_scale), br.top() + badge_radius + (4 * inv_scale))
            painter.drawEllipse(center, badge_radius, badge_radius)
            
            painter.setPen(QPen(QColor("#FFFFFF")))
            font = painter.font()
            font.setPointSizeF(font_size)
            font.setBold(True)
            painter.setFont(font)
            
            text_rect = QRectF(center.x() - badge_radius, center.y() - badge_radius, badge_radius * 2, badge_radius * 2)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(self.draw_order))

    def _get_exact_target(self):
        if not self._timed_segments or self._progress <= 0:
            return self.boundingRect().center()
        
        p = self._get_effective_progress()
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
        if getattr(self, '_is_exporting', False):
            self._smoothed_tip = target
            self._last_tip_progress = self._progress
            return target

        if not hasattr(self, '_smoothed_tip') or self._smoothed_tip is None:
            self._smoothed_tip = target
        else:
            dx = target.x() - self._smoothed_tip.x()
            dy = target.y() - self._smoothed_tip.y()
            dist = math.hypot(dx, dy)
            if dist > 350.0 or self._progress < getattr(self, '_last_tip_progress', 0.0) - 0.05:
                self._smoothed_tip = target
            else:
                alpha = 0.65
                self._smoothed_tip = QPointF(
                    self._smoothed_tip.x() + dx * alpha,
                    self._smoothed_tip.y() + dy * alpha
                )
        self._last_tip_progress = self._progress
        return self._smoothed_tip

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
            "type": "AnimatedImageItem",
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
            "anim_dir": self.anim_dir,
            "anim_easing": self.anim_easing,
            "sfx_name": getattr(self, "sfx_name", "None"),
            "sfx_volume": getattr(self, "sfx_volume", 100),
            "image_path": getattr(self, 'image_path', "")
        }

    @classmethod
    def from_dict(cls, data):
        image_path = data.get("image_path", "")
        pixmap = QPixmap(image_path) if image_path else QPixmap()
        item = cls(pixmap)
        if image_path:
            item.image_path = image_path
            
        item.setPos(data.get("x", 0), data.get("y", 0))
        item.setScale(data.get("scale", 1.0))
        item.setRotation(data.get("rotation", 0))
        item.setOpacity(data.get("opacity", 1.0))
        item._anim_duration = data.get("anim_duration", 8.0)
        item._anim_delay = data.get("anim_delay", 0.0)
        item._layer_name = data.get("layer_name", "Image")
        item.drawing_style = data.get("drawing_style", "Solid Reveal")
        item.anim_type = data.get("anim_type", "Draw")
        item.anim_dir = data.get("anim_dir", "From Left")
        item.anim_easing = data.get("anim_easing", "Linear")
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

