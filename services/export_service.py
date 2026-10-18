"""
Purpose: Background service for exporting the animation timeline to a video file.
Features: Uses QThread to prevent UI freezing. Captures the Canvas frames and pipes them to FFmpeg (or OpenCV VideoWriter) to generate an MP4.
"""
import time
from PySide6.QtCore import QThread, Signal

class ExportService(QThread):
    """
    Runs the export process in a separate background thread.
    Emits progress updates to the UI.
    """
    progress_updated = Signal(int)
    export_finished = Signal(str)
    export_error = Signal(str)

    def __init__(self, scene, output_path: str = "output.mp4", fps: int = 60, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.output_path = output_path
        self.fps = fps
        self._is_cancelled = False

    def run(self):
        try:
            self.progress_updated.emit(0)
            
            # TODO: In the actual implementation, we will step through the AnimatorEngine
            # frame by frame, call self.scene.render() into a QImage, convert to numpy array,
            # and write to a pipe connected to an FFmpeg subprocess.
            
            # For now, we simulate the heavy rendering process to test the background thread bridge.
            total_frames = 100
            for frame in range(total_frames):
                if self._is_cancelled:
                    self.export_error.emit("Export cancelled by user.")
                    return
                    
                # Simulate rendering time for one frame
                time.sleep(0.05) 
                
                # Calculate percentage
                progress = int(((frame + 1) / total_frames) * 100)
                self.progress_updated.emit(progress)
                
            self.export_finished.emit(self.output_path)
            
        except Exception as e:
            self.export_error.emit(str(e))

    def cancel(self):
        self._is_cancelled = True
