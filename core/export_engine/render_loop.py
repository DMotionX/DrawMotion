from PySide6.QtCore import QObject, Signal, QRectF, QSize, QTimer
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtWidgets import QApplication
import queue
import threading

class RenderLoop(QObject):
    """
    Handles the silent/headless rendering loop of the drawing engine.
    - Dynamically detects the Artboard bounds to avoid any white space.
    - Supports all aspect ratios (16:9, 1:1, 9:16, etc.) by reading the artboard directly.
    - Saves and restores the original engine time so the canvas looks exactly the same after export.
    """
    progress_updated = Signal(int)
    render_finished = Signal()
    render_error = Signal(str)
    
    def __init__(self, scene, engine, fps: int):
        super().__init__()
        self.scene = scene
        self.engine = engine
        self.fps = fps
        self.delta_ms = 1000.0 / self.fps
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def _get_active_artboard_info(self, time_sec: float) -> dict:
        """
        Dynamically finds the active SceneArtboardItem and any active transition based on exact absolute time.
        """
        workspace = self.engine.parent()
        if not hasattr(workspace, 'scene_windows') or not workspace.scene_windows:
            # Fallback
            artboards = [item for item in self.scene.items() if "SceneArtboardItem" in item.__class__.__name__]
            if artboards:
                artboards.sort(key=lambda a: a.pos().x())
                rect = artboards[0].mapRectToScene(artboards[0].rect())
                return {'rect': rect, 'transition': None}
            return {'rect': self.scene.sceneRect(), 'transition': None}
            
        for window in workspace.scene_windows:
            # Check for Transition
            if window['transition_start'] < time_sec < window['transition_end']:
                prev_idx = window['scene_index'] - 1
                if prev_idx >= 0 and prev_idx < len(workspace.artboards):
                    prev_board = workspace.artboards[prev_idx]
                    curr_board = workspace.artboards[window['scene_index']]
                    t_type = getattr(prev_board, 'transition_type', None)
                    t_dur = window['transition_end'] - window['transition_start']
                    t_prog = (time_sec - window['transition_start']) / t_dur if t_dur > 0 else 0
                    if t_type:
                        return {
                            'rect': prev_board.mapRectToScene(prev_board.rect()), 
                            'transition': {
                                'type': t_type,
                                'progress': t_prog,
                                'next_rect': curr_board.mapRectToScene(curr_board.rect())
                            }
                        }
                        
            # Check for Scene
            if window['start'] <= time_sec < window['end']:
                board = workspace.artboards[window['scene_index']]
                return {'rect': board.mapRectToScene(board.rect()), 'transition': None}
                
        # If time is past the end of the last window, return the last artboard
        last_board = workspace.artboards[-1]
        return {'rect': last_board.mapRectToScene(last_board.rect()), 'transition': None}

    def run_loop(self, total_frames: int, ffmpeg_manager, export_width: int, export_height: int):
        """
        Executes the render loop on the main thread, passing frames to FFmpeg.
        - Uses Producer/Consumer threading to avoid UI lag.
        - Uses a Zero-Allocation Image Pool to save memory and eliminate Garbage Collection overhead.
        """
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QImage
        from PySide6.QtCore import QSize
        import threading
        import queue
        
        self._is_cancelled = False
        self.current_frame = 0
        self.total_frames = total_frames
        self.ffmpeg_manager = ffmpeg_manager
        
        # --- FIX 1: State Restoration (Save original time) ---
        self.original_time = getattr(self.engine, 'total_time_passed', 0.0)

        # --- EXPORT ACCELERATION: Image Pool & Threads ---
        self.pool_size = 10
        self.available_images = queue.Queue(maxsize=self.pool_size)
        self.frames_to_write = queue.Queue(maxsize=self.pool_size)
        
        for _ in range(self.pool_size):
            img = QImage(QSize(export_width, export_height), QImage.Format.Format_RGBA8888)
            self.available_images.put(img)
            
        self.writer_thread_running = True
        self.writer_thread = threading.Thread(target=self._ffmpeg_writer_thread, daemon=True)
        self.writer_thread.start()
        
        if not self.engine.reset_for_export():
            self.render_error.emit("No items to animate.")
            return
            
        self.views = self.scene.views()
        
        for item in self.scene.items():
            item._is_exporting = True
        
        for view in self.views:
            view.setUpdatesEnabled(False)
            
        self.engine.blockSignals(True)
        
        QTimer.singleShot(0, self._process_batch)

    def _ffmpeg_writer_thread(self):
        """Background thread that takes images and writes them to FFmpeg pipe."""
        while self.writer_thread_running:
            try:
                # Block until an image is ready
                img = self.frames_to_write.get(timeout=0.1)
                if img is None:
                    break # Signal to stop
                
                # Write to pipe (this is slow and blocking, but we are in a background thread!)
                self.ffmpeg_manager.write_frame(img.constBits())
                
                # Return the image to the pool to be reused
                self.available_images.put(img)
                self.frames_to_write.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Writer thread error: {e}")
                break

    def _process_batch(self):
        from PySide6.QtCore import QTimer, QRectF
        from PySide6.QtGui import QColor, QPainter
        from PySide6.QtWidgets import QApplication
        import queue

        if self._is_cancelled:
            self.writer_thread_running = False
            self._cleanup_export()
            self.render_error.emit("Export cancelled by user.")
            return
            
        # Balanced export batching: matches pool size (10) for steady pipelined throughput
        batch_size = self.pool_size
        
        try:
            for _ in range(batch_size):
                if self.current_frame >= self.total_frames:
                    self._finalize_render()
                    return
                
                # Block until we have a free image from the pool
                try:
                    current_image = self.available_images.get(timeout=5.0)
                except queue.Empty:
                    if self._is_cancelled:
                        return
                    QTimer.singleShot(10, self._process_batch)
                    return
                    
                current_image.fill(QColor("white"))
                
                time_sec = getattr(self.engine, 'total_time_passed', 0.0)
                info = self._get_active_artboard_info(time_sec)
                
                painter = QPainter(current_image)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                
                self.scene.render(
                    painter,
                    target=QRectF(current_image.rect()),
                    source=info['rect']
                )
                
                t_info = info.get('transition')
                if t_info:
                    prog = t_info['progress']
                    t_type = t_info['type']
                    next_rect = t_info['next_rect']
                    
                    if t_type == 'fade':
                        painter.setOpacity(prog)
                        self.scene.render(painter, target=QRectF(current_image.rect()), source=next_rect)
                    elif t_type == 'slide':
                        pw = current_image.width()
                        offset = pw * (1.0 - prog)
                        target_rect = QRectF(offset, 0, pw, current_image.height())
                        self.scene.render(painter, target=target_rect, source=next_rect)
                    elif t_type == 'wipe':
                        pw = current_image.width()
                        clip_w = pw * prog
                        painter.setClipRect(QRectF(0, 0, clip_w, current_image.height()))
                        self.scene.render(painter, target=QRectF(current_image.rect()), source=next_rect)
                        painter.setClipping(False)
                    elif t_type == 'iris':
                        from PySide6.QtGui import QPainterPath
                        from PySide6.QtCore import QPointF
                        path = QPainterPath()
                        max_r = (current_image.width()**2 + current_image.height()**2) ** 0.5
                        radius = max_r * prog
                        cx, cy = current_image.width() / 2, current_image.height() / 2
                        path.addEllipse(QPointF(cx, cy), radius, radius)
                        painter.setClipPath(path)
                        self.scene.render(painter, target=QRectF(current_image.rect()), source=next_rect)
                        painter.setClipping(False)
                    elif t_type == 'zoom':
                        scale = prog
                        w = current_image.width() * scale
                        h = current_image.height() * scale
                        x = (current_image.width() - w) / 2
                        y = (current_image.height() - h) / 2
                        self.scene.render(painter, target=QRectF(x, y, w, h), source=next_rect)
                        
                painter.end()
                
                self.frames_to_write.put(current_image)
                
                self.current_frame += 1
                progress_pct = min(100, int((self.current_frame / self.total_frames) * 100))
                self.progress_updated.emit(progress_pct)
                
                continues = self.engine.step_manual(self.delta_ms)
                
            # Keep UI lightly responsive only once per large batch
            QApplication.processEvents()
            QTimer.singleShot(0, self._process_batch)
            
        except Exception as e:
            self.writer_thread_running = False
            self._cleanup_export()
            self.render_error.emit(str(e))

    def _finalize_render(self, final_rect=None):
        from PySide6.QtGui import QColor, QPainter
        from PySide6.QtCore import QRectF
        from PySide6.QtWidgets import QApplication

        if final_rect is None:
            final_rect = self._get_active_artboard_info(getattr(self.engine, 'total_time_passed', 0.0))['rect']
            
        # FIX: Hide the hand and add a 1-second pause at the end for a clean finish
        if hasattr(self.engine, 'hand_item') and self.engine.hand_item:
            self.engine.hand_item.hide()
            
        # Calculate how many frames make up 1 second
        # (Removed extra frames at the user's request)
        
        # Stop the writer thread gracefully
        if hasattr(self, 'writer_thread_running') and self.writer_thread_running:
            try:
                self.frames_to_write.put(None, timeout=1.0) # Signal to stop
                self.writer_thread.join(timeout=5.0)
            except Exception as e:
                print(f"Error joining writer thread: {e}")
            self.writer_thread_running = False
            
        # Prevent UI from freezing during cleanup
        QApplication.processEvents()
            
        self._cleanup_export()
        self.render_finished.emit()

    def _cleanup_export(self):
        # 2. Restore engine signals
        self.engine.blockSignals(False)
        
        for view in self.views:
            view.setUpdatesEnabled(True)
            
        # Restore UI Elements
        for item in self.scene.items():
            if hasattr(item, '_is_exporting'):
                item._is_exporting = False
            
        # --- FIX 4: State Restoration (Restore original time, not zero!) ---
        if hasattr(self.engine, 'seek'):
            self.engine.seek(self.original_time)
        
        # Update the view to reflect the restored state
        for view in self.views:
            view.update()
