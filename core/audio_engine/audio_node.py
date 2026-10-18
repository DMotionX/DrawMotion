import os
import subprocess
import re
from PySide6.QtCore import QObject, Signal, Property

class AudioNodeModel(QObject):
    duration_changed = Signal(float)
    
    def __init__(self, file_path: str, layer_name: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.layer_name = layer_name
        self._anim_duration = 5.0
        
        # Parse actual duration using imageio_ffmpeg
        if os.path.exists(file_path):
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            
            if os.path.exists(ffmpeg_path):
                try:
                    # CREATE_NO_WINDOW = 0x08000000 to prevent terminal flashes on Windows
                    result = subprocess.run(
                        [ffmpeg_path, "-i", file_path],
                        capture_output=True, text=True,
                        encoding='utf-8', errors='replace',
                        stdin=subprocess.DEVNULL,
                        creationflags=0x08000000
                    )
                    match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", result.stderr)
                    if match:
                        h, m, s = match.groups()
                        self._anim_duration = int(h) * 3600 + int(m) * 60 + float(s)
                except Exception:
                    pass
        self._anim_delay = 0.0
        self._base_duration = self._anim_duration
        self.audio_fx_settings = {
            "volume": 100,
            "denoise": False,
            "normalize": False,
            "speed": 1.0,
            "pitch": False,
            "fade_in": 0.0,
            "fade_out": 0.0
        }
        
    @Property(float)
    def anim_duration(self):
        return self._anim_duration
        
    @anim_duration.setter
    def anim_duration(self, v):
        self._anim_duration = v
        self.duration_changed.emit(v)
        
    @Property(float)
    def anim_delay(self):
        return self._anim_delay
        
    @anim_delay.setter
    def anim_delay(self, v):
        self._anim_delay = v

    def to_dict(self):
        return {
            "type": "AudioNodeModel",
            "file_path": self.file_path,
            "layer_name": self.layer_name,
            "anim_duration": self._anim_duration,
            "anim_delay": self._anim_delay,
            "audio_fx_settings": getattr(self, 'audio_fx_settings', {})
        }
        
    @classmethod
    def from_dict(cls, data):
        node = cls(data.get("file_path", ""), data.get("layer_name", "Voice"))
        node.anim_duration = data.get("anim_duration", 5.0)
        node.anim_delay = data.get("anim_delay", 0.0)
        saved_fx = data.get("audio_fx_settings")
        if isinstance(saved_fx, dict):
            node.audio_fx_settings = dict(saved_fx)
            saved_speed = float(node.audio_fx_settings.get("speed", 1.0))
            if saved_speed > 0:
                node._base_duration = node.anim_duration * saved_speed
            else:
                node._base_duration = node.anim_duration
        else:
            node._base_duration = node.anim_duration
        return node
