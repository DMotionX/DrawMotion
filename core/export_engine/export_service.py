from PySide6.QtCore import QObject, Signal
from .ffmpeg_manager import FFmpegManager
from .render_loop import RenderLoop

# Resolution presets mapping label -> (width, height)
RESOLUTION_PRESETS = {
    "1080p (FHD)": (1920, 1080),
    "720p (HD)":   (1280, 720),
    "4K (UHD)":    (3840, 2160),
}

class ExportService(QObject):
    """
    Main Coordinator for the Export Engine.
    - Reads the Artboard dimensions dynamically at export time.
    - Applies the chosen resolution preset to scale the output.
    - Glues together the FFmpegManager and the RenderLoop.
    """
    progress_updated = Signal(int)
    export_finished = Signal(str)
    export_error = Signal(str)
    
    def __init__(self, scene, engine, user_items, audio_items, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.engine = engine
        self.user_items = user_items
        self.audio_items = audio_items
        self.fps = 60
        self._current_ffmpeg_manager = None
        self._current_output_path = None
        
        # RenderLoop no longer needs fixed width/height at init — it reads artboard dynamically
        self.render_loop = RenderLoop(scene, engine, self.fps)
        self.render_loop.progress_updated.connect(self.progress_updated.emit)
        self.render_loop.render_finished.connect(self._on_render_finished)
        self.render_loop.render_error.connect(self._on_render_error)

    def cancel(self):
        self.render_loop.cancel()

    def _get_export_resolution(self, resolution_label: str):
        """
        Calculates dynamic export resolution based on Artboard aspect ratio
        and the chosen quality preset.
        """
        base_w, base_h = 1920, 1080
        if resolution_label in RESOLUTION_PRESETS:
            base_w, base_h = RESOLUTION_PRESETS[resolution_label]
            
        art_w, art_h = self._get_artboard_native_size()
        
        # The shorter dimension of the preset determines the 'quality' (e.g. 1080 for 1080p)
        quality_dim = min(base_w, base_h)
        aspect = art_w / float(art_h) if art_h > 0 else 1.0
        
        if aspect >= 1.0: # Landscape or Square
            export_h = quality_dim
            export_w = int(quality_dim * aspect)
        else: # Portrait
            export_w = quality_dim
            export_h = int(quality_dim / aspect)
            
        # Ensure dimensions are even (H264 codec requirement)
        export_w = export_w if export_w % 2 == 0 else export_w + 1
        export_h = export_h if export_h % 2 == 0 else export_h + 1
        
        return export_w, export_h

    def _get_artboard_native_size(self):
        """Reads the artboard's true geometric size (ignoring bleeding children)."""
        try:
            for item in self.scene.items():
                if "SceneArtboardItem" in item.__class__.__name__:
                    r = item.rect() # We use rect(), NOT sceneBoundingRect()!
                    return int(r.width()), int(r.height())
        except Exception:
            pass
        return 1920, 1080  # Safe fallback

    def start_export(self, output_path: str, resolution_label: str = "1080p (FHD)", fps: int = 30):
        # Determine the final pixel dimensions based on user's resolution choice
        export_width, export_height = self._get_export_resolution(resolution_label)
        
        self.fps = fps # Update internal FPS so RenderLoop and calculations use it
        self.render_loop.fps = fps # Update render loop fps
        self.render_loop.delta_ms = 1000.0 / fps # FIX: use float for perfect precision
        
        # Compile schedule temporarily to extract SFX timings
        if not self.engine.schedule:
            self.engine.schedule = self.engine.scheduler.compile(self.engine.queue)
        sfx_items = self.engine.get_sfx_schedule()
        
        self._current_ffmpeg_manager = FFmpegManager(export_width, export_height, fps, audio_items=self.audio_items, sfx_items=sfx_items)
        self._current_output_path = output_path
        
        try:
            # 1. Calculate Total Time from the actual Multi-Scene Workspace Timeline
            workspace = self.engine.parent()
            
            if hasattr(workspace, 'scene_windows') and workspace.scene_windows:
                # The true duration of the entire project is the end time of the last scene window
                total_time_sec = workspace.scene_windows[-1]['end']
            else:
                # Fallback to compiled schedule if workspace windows aren't available
                compiled_schedule = self.engine.scheduler.compile(self.user_items)
                if compiled_schedule:
                    end_times = [action['end'] for action in compiled_schedule]
                    total_time_sec = max(end_times) if end_times else 1.0
                else:
                    total_time_sec = 1.0
                    
            total_time_sec = max(1.0, total_time_sec)
            # Add 1.0 second extra delay at the end to allow the hand to hide and for a clean video finish
            total_time_sec += 1.0
            
            total_frames = int(total_time_sec * self.fps)
            
            # 2. Start FFmpeg at the correct output resolution with strict duration
            if not self._current_ffmpeg_manager.start_process(output_path, total_time_sec=total_time_sec):
                self.export_error.emit("Failed to initialize FFmpeg for export.")
                return
            
            # 2.5 Ensure the animator engine's queue is fully synchronized before exporting
            # This fixes the "No items to animate" error when exporting immediately after loading a project.
            sorted_items = sorted(self.user_items, key=lambda x: (getattr(x, 'anim_delay', 0.0), getattr(x, 'zValue', lambda: 0)()))
            self.engine.sync_queue(sorted_items, force_recompile=True)
            
            # 3. Run the Render Loop — this starts a QTimer loop and returns IMMEDIATELY
            self.render_loop.run_loop(total_frames, self._current_ffmpeg_manager, export_width, export_height)
            
            # NOTE: Do NOT finalize FFmpeg here. Wait for the `render_finished` signal.
            
        except InterruptedError as e:
            if self._current_ffmpeg_manager:
                self._current_ffmpeg_manager.terminate()
            self.export_error.emit(str(e))
        except Exception as e:
            if self._current_ffmpeg_manager:
                self._current_ffmpeg_manager.terminate()
            self.export_error.emit(str(e))

    def _on_render_finished(self):
        """Called asynchronously when RenderLoop completes its QTimer batches."""
        if self._current_ffmpeg_manager:
            try:
                self._current_ffmpeg_manager.finalize()
            except Exception as e:
                self.export_error.emit(f"FFmpeg finalize error: {e}")
                return
                
        if self._current_output_path:
            self.export_finished.emit(self._current_output_path)
            
        self._current_ffmpeg_manager = None
        self._current_output_path = None

    def _on_render_error(self, error_msg: str):
        """Called asynchronously if RenderLoop encounters an error."""
        if self._current_ffmpeg_manager:
            self._current_ffmpeg_manager.terminate()
            self._current_ffmpeg_manager = None
        self._current_output_path = None
        self.export_error.emit(error_msg)
